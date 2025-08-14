"""
multitool.py
============

Универсальная точка входа для интеграции сторонних API и инструментов.
Здесь добавлен простой реестр доступных инструментов/воркфлоу/приложений
в памяти процесса для того, чтобы система знала о доступных ресурсах.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import threading

# Простейший реестр в памяти (для durably — см. БД/файлы)
_REGISTRY_LOCK = threading.Lock()
_REGISTRY: Dict[str, Dict[str, Any]] = {
    "tools": {},       # name -> {meta}
    "workflows": {},   # id -> {meta}
    "apps": {},        # id -> {meta}
}


def call(api_name: str, params: Dict[str, Any]) -> Any:
    """Заглушка вызова внешнего API по имени. Реальная логика подменяется.

    Здесь оставляем совместимость со старыми вызовами.
    """
    return {"api": api_name, "called": True, "params": params}


# -------------------------------
# Registry API
# -------------------------------

def register_tool(name: str, meta: Optional[Dict[str, Any]] = None) -> None:
    with _REGISTRY_LOCK:
        _REGISTRY["tools"][name] = meta or {}

def list_tools() -> Dict[str, Dict[str, Any]]:
    with _REGISTRY_LOCK:
        return dict(_REGISTRY["tools"])  # copy

def register_workflow(wf_id: str, meta: Optional[Dict[str, Any]] = None) -> None:
    with _REGISTRY_LOCK:
        _REGISTRY["workflows"][wf_id] = meta or {}

def list_workflows() -> Dict[str, Dict[str, Any]]:
    with _REGISTRY_LOCK:
        return dict(_REGISTRY["workflows"])  # copy

def register_app(app_id: str, meta: Optional[Dict[str, Any]] = None) -> None:
    with _REGISTRY_LOCK:
        _REGISTRY["apps"][app_id] = meta or {}

def list_apps() -> Dict[str, Dict[str, Any]]:
    with _REGISTRY_LOCK:
        return dict(_REGISTRY["apps"])  # copy
