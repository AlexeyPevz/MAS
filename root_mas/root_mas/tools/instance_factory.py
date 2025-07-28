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


REPO_ROOT = Path(__file__).resolve().parents[1]


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
    with inst_cfg_path.open("r", encoding="utf-8") as f:
        inst_data = yaml.safe_load(f) or {}
    insts = inst_data.setdefault("instances", {})
    insts[instance_name] = {
        "type": instance_type,
        "endpoint": env_vars.get("MAS_ENDPOINT", ""),
    }
    with inst_cfg_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(inst_data, f, allow_unicode=True)