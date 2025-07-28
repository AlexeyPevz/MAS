"""
security.py
===========

Заготовка для управления секретами и безопасностью. Реализация
включает функции для получения секретов из Vault (или другого
секрет‑менеджера) и механизм подтверждения изменений глобальных
промптов через Telegram. Пока реализованы только заглушки.
"""

from typing import Optional
import os
from pathlib import Path
import yaml  # type: ignore
import time
import threading
from typing import Dict

# hvac является официальным Python-SDK для HashiCorp Vault
try:
    import hvac  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    hvac = None  # type: ignore

from .callbacks import outgoing_to_telegram

# ---------------------------------------------------------------------------
# Vault helpers
# ---------------------------------------------------------------------------

_VAULT_CLIENT: "hvac.Client | None" = None  # глобальный клиент, ленивое создание
_VAULT_LOCK = threading.Lock()

# Кэш прочитанных секретов: key -> (expire_ts, value)
_CACHE: Dict[str, tuple[float, str]] = {}
_CACHE_TTL = float(os.getenv("VAULT_CACHE_TTL", "300"))  # сек


def _get_vault_client() -> "hvac.Client | None":  # noqa: D401
    """Lazy-init Vault client with optional auto-renew token."""

    global _VAULT_CLIENT
    if hvac is None:
        return None

    with _VAULT_LOCK:
        if _VAULT_CLIENT is not None:
            return _VAULT_CLIENT

        addr = os.getenv("VAULT_ADDR")
        token = os.getenv("VAULT_TOKEN")
        if not addr or not token:
            return None

        client = hvac.Client(url=addr, token=token)

        # Попытка авто-renew, если TTL < 30% от max
        try:
            lookup = client.auth.token.lookup_self()["data"]  # type: ignore[index]
            ttl = lookup.get("ttl", 0)
            renewable = lookup.get("renewable", False)
            if renewable and ttl and ttl < lookup.get("creation_ttl", 0) * 0.3:
                client.auth.token.renew_self()
        except Exception:  # pragma: no cover - network errors
            pass

        _VAULT_CLIENT = client
        return client


def get_secret(key: str) -> Optional[str]:
    """Получить секрет по ключу из Vault, env или локального файла."""

    # Сначала пробуем прочитать из переменных окружения
    if val := os.getenv(key):
        return val

    # Попытка получить из Vault
    client = _get_vault_client()
    path = os.getenv("VAULT_PATH", "secret/data/mas")

    if client is not None:
        # Проверяем кэш
        now = time.time()
        cached = _CACHE.get(key)
        if cached and cached[0] > now:
            return cached[1]

        try:
            result = client.secrets.kv.v2.read_secret_version(path=path)
            data = result.get("data", {}).get("data", {})  # type: ignore[index]
            if isinstance(data, dict) and key in data:
                _CACHE[key] = (now + _CACHE_TTL, str(data[key]))
                return str(data[key])
        except Exception as exc:  # pragma: no cover - network errors
            print(f"[Security] Vault error: {exc}")

    # Затем ищем файл ~/.mas_secrets.yaml, в котором могут храниться ключи
    secrets_file = Path.home() / ".mas_secrets.yaml"
    if secrets_file.exists():
        try:
            data = yaml.safe_load(secrets_file.read_text(encoding="utf-8")) or {}
            if isinstance(data, dict):
                return data.get(key)
        except Exception:
            return None

    return None


def approve_global_prompt_change(diff: str) -> bool:
    """Запросить у пользователя подтверждение на изменение глобального промпта."""

    message = (
        "[Security] Требуется подтверждение изменения глобального промпта:\n" + diff
    )
    try:
        outgoing_to_telegram(message)
    except Exception:
        pass

    print(message)
    try:
        answer = input("Apply changes? [y/N]: ").strip().lower()
    except KeyboardInterrupt:
        return False
    return answer in {"y", "yes"}


class SecurityGuard:
    """Simple guard that validates potentially dangerous operations."""

    banned_commands = {"rm", "sudo", "apt-get", "docker", "bash", "sh"}

    def is_command_allowed(self, command: str | list[str]) -> bool:
        tokens = command if isinstance(command, list) else str(command).split()
        return not any(tok in self.banned_commands for tok in tokens)

    def check_shell(self, command: str | list[str]) -> None:
        if not self.is_command_allowed(command):
            raise PermissionError(f"shell access denied: {command}")


security_guard = SecurityGuard()
