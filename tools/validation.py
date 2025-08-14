"""
validation.py
=============

Лёгкие проверки входных спецификаций без внешних зависимостей.
Функции возвращают кортеж (ok: bool, message: str) для логирования.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple


def _is_str(x: Any) -> bool:
	return isinstance(x, str)


def _is_dict(x: Any) -> bool:
	return isinstance(x, dict)


def _is_list(x: Any) -> bool:
	return isinstance(x, list)


def validate_workflow_spec(spec: Any) -> Tuple[bool, str]:
	"""Проверка спецификации workflow.
	Допускается:
	- Полный JSON n8n (dict с ключом "nodes")
	- Упрощённый DSL: {"steps": [ {"name": str, "type": str, "parameters": dict} ]}
	- Любая строка (fallback: будет обёрнута в минимальный workflow)
	"""
	# Строка — допустимо, создадим минимальный workflow
	if _is_str(spec):
		return True, "string spec (will use fallback workflow)"
	# Полный JSON n8n
	if _is_dict(spec) and "nodes" in spec:
		if _is_list(spec.get("nodes")):
			return True, "n8n json"
		return False, "n8n json missing 'nodes' list"
	# DSL steps
	if _is_dict(spec) and "steps" in spec:
		steps = spec.get("steps")
		if not _is_list(steps):
			return False, "steps is not a list"
		for idx, s in enumerate(steps):
			if not _is_dict(s):
				return False, f"step[{idx}] is not an object"
			if not _is_str(s.get("name", "")):
				return False, f"step[{idx}].name must be string"
			if not _is_str(s.get("type", "")):
				return False, f"step[{idx}].type must be string"
			if s.get("parameters") is not None and not _is_dict(s.get("parameters")):
				return False, f"step[{idx}].parameters must be object"
		return True, "dsl steps"
	return False, "invalid workflow spec"


def validate_app_spec(spec: Dict[str, Any]) -> Tuple[bool, str]:
	"""Проверка спецификации приложения для GPT‑Pilot.
	Минимум: объект с ключами name (str) и components (list|optional).
	"""
	if not _is_dict(spec):
		return False, "spec must be object"
	name = spec.get("name")
	if not _is_str(name) or not name.strip():
		return False, "name is required string"
	components = spec.get("components")
	if components is not None and not _is_list(components):
		return False, "components must be array if provided"
	return True, "ok"


def validate_tool_params(params: Dict[str, Any]) -> Tuple[bool, str]:
	"""Проверка параметров регистрации инструмента.
	Минимум: api_name (str). docs_url (str, optional), auth (object, optional).
	"""
	if not _is_dict(params):
		return False, "params must be object"
	api_name = params.get("api_name") or params.get("name")
	if not _is_str(api_name) or not api_name.strip():
		return False, "api_name (or name) is required string"
	docs_url = params.get("docs_url")
	if docs_url is not None and not _is_str(docs_url):
		return False, "docs_url must be string if provided"
	auth = params.get("auth")
	if auth is not None and not _is_dict(auth):
		return False, "auth must be object if provided"
	return True, "ok"