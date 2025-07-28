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

    def add_job(self, func: Callable[[], Any], interval: int, run_immediately: bool = False) -> None:
        """Добавить задачу, запускаемую каждые `interval` секунд."""
        job = self.scheduler.every(interval).seconds.do(func)
        if run_immediately:
            job.next_run = self.scheduler.datetime.datetime.now()

    def run_forever(self) -> None:
        """Запустить цикл выполнения задач."""
        logging.info("[cron] запуск планировщика задач…")
        while True:
            self.scheduler.run_pending()
            time.sleep(1)

    def run_pending(self) -> None:
        """Выполнить все задачи, запланированные на данный момент."""
        self.scheduler.run_pending()
