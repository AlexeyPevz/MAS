"""
fact_checker.py
===============

Заготовка для агента Fact‑Checker. Предоставляет функции для проверки
достоверности информации и источников. Реальная реализация может
использовать дополнительные API, библиотеки для детектирования фейков и
кросс‑проверку по нескольким источникам. Здесь реализована простая
валидация на наличие ключевых слов.
"""

from typing import List, Dict, Any
import logging
import json
import hashlib
import os
from typing import Tuple


# Импорт OpenAI (используется как универсальный клиент для OpenRouter)
try:
    from openai import OpenAI  # OpenAI client можно использовать с любым OpenAI-совместимым API
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None  # type: ignore

try:
    from memory.redis_store import RedisStore

    _REDIS = RedisStore()
except Exception:  # pragma: no cover
    _REDIS = None  # type: ignore


def _cache_get(key: str) -> Tuple[bool, list[str]] | None:  # noqa: D401
    if _REDIS is None:
        return None
    data = _REDIS.get(key)
    if data:
        try:
            flag, issues = json.loads(data)
            return bool(flag), issues
        except Exception:
            return None
    return None


def _cache_set(key: str, value: Tuple[bool, list[str]], ttl: int = 86400) -> None:
    if _REDIS is None:
        return
    try:
        _REDIS.set(key, json.dumps(value, ensure_ascii=False), ttl)
    except Exception:
        pass


def _hash_sources(sources: List[Dict[str, Any]]) -> str:
    m = hashlib.sha256()
    m.update(json.dumps(sources, sort_keys=True).encode("utf-8"))
    return m.hexdigest()


def _gpt_validate(sources: List[Dict[str, Any]]) -> Tuple[bool, list[str]]:
    if OpenAI is None:
        raise RuntimeError("OpenAI package not available")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    openai_client = OpenAI(api_key=api_key)
    prompt = (
        "You are a fact-checker. Evaluate the reliability of the following sources.\n"
        "Return JSON with keys 'valid' (true/false) and 'issues' (array of strings).\n"
        f"Sources:\n{json.dumps(sources, ensure_ascii=False, indent=2)}"
    )
    try:
        resp = openai_client.chat.completions.create(
            model=os.getenv("FACTCHECK_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = resp.choices[0].message["content"]  # type: ignore[index]
        data = json.loads(content)
        return bool(data.get("valid", False)), data.get("issues", [])
    except Exception as exc:
        logging.warning("[FactChecker] GPT validation error: %s", exc)
        raise


def _heuristic_validate(sources: List[Dict[str, Any]]) -> Tuple[bool, list[str]]:
    bad_keywords = ["clickbait", "fake", "suspicious"]
    issues: list[str] = []
    for src in sources:
        url = src.get("url", "")
        title = src.get("title", "")
        if not url.startswith("https://"):
            issues.append(f"Insecure URL: {url}")
        for word in bad_keywords:
            if word in url.lower() or word in title.lower():
                issues.append(f"Potentially unreliable ({word}) in {url}")
    return (not issues), issues


def validate_sources(sources: List[Dict[str, Any]]) -> bool:
    """Validate list of sources using GPT (fallback heuristic)."""

    key = f"fact:{_hash_sources(sources)}"
    cached = _cache_get(key)
    if cached is not None:
        return cached[0]

    try:
        valid, issues = _gpt_validate(sources)
    except Exception:
        valid, issues = _heuristic_validate(sources)

    _cache_set(key, (valid, issues))
    if not valid:
        logging.info("[FactChecker] issues: %s", issues)
    return valid


def check_facts(results: List[Dict[str, Any]]) -> bool:
    """Проверить факты на основе сниппетов."""

    snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
    if len(snippets) < 2:
        logging.info("[FactChecker] недостаточно данных для кросс-проверки")
        return False
    return cross_reference(snippets)


def cross_reference(snippets: List[str]) -> bool:
    """Проверить совпадения фраз в нескольких источниках."""

    seen = set()
    for text in snippets:
        key = text.strip().lower()[:50]
        if key in seen:
            return True
        seen.add(key)
    return False