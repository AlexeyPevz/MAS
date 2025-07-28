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

try:
    import hvac  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    hvac = None  # type: ignore

from .callbacks import outgoing_to_telegram


def get_secret(key: str) -> Optional[str]:
    """Получить секрет по ключу из Vault, env или локального файла."""

    # Сначала пробуем прочитать из переменных окружения
    if val := os.getenv(key):
        return val

    # Если настроен Vault и установлен hvac, пробуем получить секрет оттуда
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    path = os.getenv("VAULT_PATH", "secret/data/mas")
    if hvac is not None and addr and token:
        try:
            client = hvac.Client(url=addr, token=token)
            result = client.secrets.kv.v2.read_secret_version(path=path)
            data = result.get("data", {}).get("data", {})
            if isinstance(data, dict) and key in data:
                return data[key]
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
