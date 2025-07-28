"""
cron.py
=======

Простейший планировщик задач для MAS. Использует библиотеку `schedule`
для периодического вызова функций. Агент Coordination может запускать
эти задачи, чтобы проверять очередь заданий, выполнять опрос внешних
сервисов и инициировать события.

Для использования установите библиотеку schedule: `pip install schedule`.
"""

from typing import Callable, Any
import time
import logging

try:
    import schedule  # type: ignore
except ImportError:
    schedule = None  # type: ignore


class CronScheduler:
    def __init__(self) -> None:
        if schedule is None:
            raise RuntimeError("Для работы CronScheduler требуется библиотека schedule. Установите её: pip install schedule")
        self.scheduler = schedule

    def add_job(self, func: Callable[[], Any], interval: int) -> None:
        """Добавить задачу, запускаемую каждые `interval` секунд."""
        self.scheduler.every(interval).seconds.do(func)

    def run_forever(self) -> None:
        """Запустить цикл выполнения задач."""
        logging.info("[cron] запуск планировщика задач…")
        while True:
            self.scheduler.run_pending()
            time.sleep(1)


def _heartbeat() -> None:
    """Простая демонстрационная задача."""
    logging.info("[cron] heartbeat")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cron = CronScheduler()
    cron.add_job(_heartbeat, 60)
    cron.run_forever()