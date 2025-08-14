"""
multitool.py
============

Универсальная точка входа для интеграции сторонних API и инструментов.
Здесь добавлен простой реестр доступных инструментов/воркфлоу/приложений
в памяти процесса для того, чтобы система знала о доступных ресурсах.
Поддерживается версионирование с ограничением числа хранимых версий и
персистентность на диск (data/registry.json) или в Redis (опционально).
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import threading
import json
from pathlib import Path
from datetime import datetime, timezone
import os

try:
	import redis  # type: ignore
	_HAS_REDIS = True
except Exception:
	redis = None  # type: ignore
	_HAS_REDIS = False

# Простейший версионируемый реестр с персистентностью
_REGISTRY_LOCK = threading.Lock()
_REGISTRY_PATH = Path("data") / "registry.json"
_REGISTRY: Dict[str, Dict[str, Any]] = {
	"tools": {},       # key -> {current_version:int, versions: {str->meta}, max_versions:int}
	"workflows": {},   # key -> {current_version:int, versions: {str->meta}, max_versions:int}
	"apps": {},        # key -> {current_version:int, versions: {str->meta}, max_versions:int}
}
_DEFAULT_MAX_VERSIONS = 5

# Backend selection
_REGISTRY_BACKEND = os.getenv("REGISTRY_BACKEND", "file").lower()
_redis_client: Optional["redis.Redis"] = None


def _init_redis() -> None:
	global _redis_client, _REGISTRY_BACKEND
	if _REGISTRY_BACKEND != "redis":
		return
	if not _HAS_REDIS:
		_REGISTRY_BACKEND = "file"
		return
	try:
		_redis_client = redis.Redis(
			host=os.getenv("REDIS_HOST", "localhost"),
			port=int(os.getenv("REDIS_PORT", "6379")),
			db=int(os.getenv("REGISTRY_REDIS_DB", "0")),
			decode_responses=True,
		)
		_redis_client.ping()
	except Exception:
		_redis_client = None
		_REGISTRY_BACKEND = "file"


_init_redis()


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _ensure_data_dir() -> None:
	_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def _save_registry() -> None:
	# Redis backend
	if _REGISTRY_BACKEND == "redis" and _redis_client is not None:
		try:
			with _REGISTRY_LOCK:
				for cat in ("tools", "workflows", "apps"):
					_redis_client.set(f"registry:{cat}", json.dumps(_REGISTRY.get(cat, {}), ensure_ascii=False))
			return
		except Exception:
			pass  # fallback to file
	# File backend
	_ensure_data_dir()
	tmp = {"tools": {}, "workflows": {}, "apps": {}}
	for cat in ("tools", "workflows", "apps"):
		tmp[cat] = _REGISTRY.get(cat, {})
	with _REGISTRY_PATH.open("w", encoding="utf-8") as f:
		json.dump(tmp, f, indent=2, ensure_ascii=False)


def _load_registry() -> None:
	# Redis backend
	if _REGISTRY_BACKEND == "redis" and _redis_client is not None:
		try:
			with _REGISTRY_LOCK:
				for cat in ("tools", "workflows", "apps"):
					val = _redis_client.get(f"registry:{cat}")
					if val:
						_REGISTRY[cat] = json.loads(val)
			return
		except Exception:
			pass  # fallback to file
	# File backend
	if not _REGISTRY_PATH.exists():
		return
	try:
		with _REGISTRY_PATH.open("r", encoding="utf-8") as f:
			data = json.load(f)
		with _REGISTRY_LOCK:
			for cat in ("tools", "workflows", "apps"):
				if isinstance(data.get(cat), dict):
					_REGISTRY[cat] = data[cat]
	except Exception:
		# Игнорируем повреждения файла, начнём с пустого
		pass


_load_registry()


def call(api_name: str, params: Dict[str, Any]) -> Any:
	"""Заглушка вызова внешнего API по имени. Реальная логика подменяется."""
	return {"api": api_name, "called": True, "params": params}


# -------------------------------
# Versioned Registry API (generic)
# -------------------------------

def _bump_version(entry: Dict[str, Any], meta: Dict[str, Any], max_versions: int) -> Dict[str, Any]:
	versions: Dict[str, Any] = entry.setdefault("versions", {})
	current = int(entry.get("current_version", 0)) + 1
	entry["current_version"] = current
	versions[str(current)] = meta
	entry["max_versions"] = max_versions
	# Обрезаем старые версии
	keys = sorted((int(k) for k in versions.keys()))
	while len(keys) > max_versions:
		oldest = str(keys.pop(0))
		versions.pop(oldest, None)
	return entry


def _register_version(category: str, key: str, meta: Dict[str, Any], max_versions: int = _DEFAULT_MAX_VERSIONS) -> None:
	with _REGISTRY_LOCK:
		cat = _REGISTRY.setdefault(category, {})
		entry = cat.get(key, {"current_version": 0, "versions": {}, "max_versions": max_versions})
		meta = dict(meta or {})
		meta.setdefault("registered_at", _now_iso())
		cat[key] = _bump_version(entry, meta, max_versions)
		_save_registry()


def _list_current(category: str) -> Dict[str, Dict[str, Any]]:
	with _REGISTRY_LOCK:
		result: Dict[str, Dict[str, Any]] = {}
		cat = _REGISTRY.get(category, {})
		for key, entry in cat.items():
			current = str(entry.get("current_version", ""))
			current_meta = entry.get("versions", {}).get(current, {})
			result[key] = {
				"current_version": entry.get("current_version", 0),
				"meta": current_meta,
			}
		return result


def _get_versions(category: str, key: str) -> Dict[str, Any]:
	with _REGISTRY_LOCK:
		entry = _REGISTRY.get(category, {}).get(key)
		if not entry:
			return {}
		return {
			"current_version": entry.get("current_version", 0),
			"versions": dict(entry.get("versions", {})),
			"max_versions": entry.get("max_versions", _DEFAULT_MAX_VERSIONS),
		}


def _rollback(category: str, key: str, target_version: Optional[int] = None) -> bool:
	with _REGISTRY_LOCK:
		entry = _REGISTRY.get(category, {}).get(key)
		if not entry:
			return False
		versions = entry.get("versions", {})
		current = int(entry.get("current_version", 0))
		if target_version is None:
			target = current - 1
		else:
			target = int(target_version)
		if target < 1 or str(target) not in versions:
			return False
		entry["current_version"] = target
		_save_registry()
		return True


# -------------------------------
# Category-specific helpers
# -------------------------------

def register_tool_version(name: str, meta: Optional[Dict[str, Any]] = None, max_versions: int = _DEFAULT_MAX_VERSIONS) -> None:
	_register_version("tools", name, meta or {}, max_versions)


def list_tools() -> Dict[str, Dict[str, Any]]:
	return _list_current("tools")


def get_tool_versions(name: str) -> Dict[str, Any]:
	return _get_versions("tools", name)


def rollback_tool(name: str, target_version: Optional[int] = None) -> bool:
	return _rollback("tools", name, target_version)


def register_workflow_version(key: str, meta: Optional[Dict[str, Any]] = None, max_versions: int = _DEFAULT_MAX_VERSIONS) -> None:
	_register_version("workflows", key, meta or {}, max_versions)


def list_workflows() -> Dict[str, Dict[str, Any]]:
	return _list_current("workflows")


def get_workflow_versions(key: str) -> Dict[str, Any]:
	return _get_versions("workflows", key)


def rollback_workflow(key: str, target_version: Optional[int] = None) -> bool:
	return _rollback("workflows", key, target_version)


def register_app_version(key: str, meta: Optional[Dict[str, Any]] = None, max_versions: int = _DEFAULT_MAX_VERSIONS) -> None:
	_register_version("apps", key, meta or {}, max_versions)


def list_apps() -> Dict[str, Dict[str, Any]]:
	return _list_current("apps")


def get_app_versions(key: str) -> Dict[str, Any]:
	return _get_versions("apps", key)


def rollback_app(key: str, target_version: Optional[int] = None) -> bool:
	return _rollback("apps", key, target_version)
