"""
logging_setup.py
================

Модуль для конфигурации логирования в Root MAS. Настраивает логирование
в консоль и в файл. Журнал можно затем анализировать в AutoGen Studio
или других инструментах наблюдаемости.
"""

import logging
from pathlib import Path


def configure_logging(log_dir: str = "logs", level: int = logging.INFO) -> None:
    """Настроить логирование.

    Args:
        log_dir: папка для хранения лог‑файлов
        level: уровень логирования
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / "mas.log"
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )