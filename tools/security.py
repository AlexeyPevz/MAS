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


def get_secret(key: str) -> Optional[str]:
    """Получить секрет по ключу из хранилища или переменных окружения."""

    # Сначала пробуем прочитать из переменных окружения
    if val := os.getenv(key):
        return val

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

    print("[Security] Требуется подтверждение изменения глобального промпта:")
    print(diff)
    try:
        answer = input("Apply changes? [y/N]: ").strip().lower()
    except KeyboardInterrupt:
        return False
    return answer in {"y", "yes"}