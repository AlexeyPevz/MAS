"""
instance_factory.py
===================

Модуль для развёртывания новых инстансов MAS. Функция `deploy_instance`
создаёт файл `.env` с указанными переменными окружения, запускает
docker‑compose и регистрирует endpoint в `config/instances.yaml`.
"""

import os
import subprocess
import yaml  # type: ignore
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .security import get_secret


REPO_ROOT = Path(__file__).resolve().parents[1]


def auto_deploy_instance(instance_type: str = "internal", env_vars: Dict[str, str] | None = None) -> str:
    """Automatically deploy an instance and register it.

    A unique instance name is generated based on the current UTC timestamp.
    Missing environment variables are fetched via :func:`get_secret`.

    Args:
        instance_type: Either ``internal`` or ``client``.
        env_vars: Optional base environment variables for the ``.env`` file.

    Returns:
        The name of the created instance.
    """

    instance_name = f"{instance_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    env = env_vars.copy() if env_vars else {}

    for key in [
        "OPENROUTER_API_KEY",
        "YANDEX_API_KEY",
        "YANDEX_FOLDER_ID",
        "N8N_API_TOKEN",
        "TELEGRAM_BOT_TOKEN",
    ]:
        if key not in env:
            secret = get_secret(key)
            if secret:
                env[key] = secret

    env.setdefault("MAS_ENDPOINT", f"http://localhost:8000/{instance_name}")

    deploy_instance(f"deploy/{instance_type}", env, instance_name, instance_type)
    return instance_name


def deploy_instance(directory: str, env_vars: Dict[str, str], instance_name: str, instance_type: str = "internal") -> None:
    """Развернуть новый MAS‑инстанс.

    Args:
        directory: относительный путь к директории развертывания (deploy/internal или deploy/client)
        env_vars: словарь переменных окружения для .env
        instance_name: название инстанса (ключ в config/instances.yaml)
        instance_type: тип инстанса (internal или client)
    """
    deploy_dir = REPO_ROOT / directory
    env_path = deploy_dir / ".env"
    # Создаём .env файл
    with env_path.open("w", encoding="utf-8") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")
    # Запускаем docker compose up -d
    subprocess.run(["docker", "compose", "up", "-d"], cwd=str(deploy_dir))
    # Регистрируем инстанс в config/instances.yaml
    inst_cfg_path = REPO_ROOT / "config" / "instances.yaml"
    if inst_cfg_path.exists():
        with inst_cfg_path.open("r", encoding="utf-8") as f:
            inst_data = yaml.safe_load(f) or {}
    else:
        inst_data = {}
    insts = inst_data.setdefault("instances", {})
    insts[instance_name] = {
        "type": instance_type,
        "endpoint": env_vars.get("MAS_ENDPOINT", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "status": "running",
    }
    with inst_cfg_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(inst_data, f, allow_unicode=True)