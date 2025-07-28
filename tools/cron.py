"""
cron.py
=======

Простейший планировщик задач для MAS. Использует библиотеку `schedule`
для периодического вызова функций. Агент Coordination может запускать
эти задачи, чтобы проверять очередь заданий, выполнять опрос внешних
сервисов и инициировать события.

Для использования установите библиотеку schedule: `pip install schedule`.
"""

from typing import Callable, Any, Dict, Optional
import time
import logging
import json

from .callback_matrix import handle_event
from memory.redis_store import RedisStore

try:
    import schedule  # type: ignore
except ImportError:
    schedule = None  # type: ignore


class CronScheduler:
    """Простой cron-планировщик с опциональным хранением задач в Redis."""

    def __init__(self, store: Optional[RedisStore] = None) -> None:
        if schedule is None:
            raise RuntimeError(
                "Для работы CronScheduler требуется библиотека schedule. Установите её: pip install schedule"
            )
        self.scheduler = schedule
        self.store = store
        self.jobs: Dict[str, Any] = {}
        if self.store is not None:
            self._restore_jobs()

    def _restore_jobs(self) -> None:
        """Восстановить сохранённые задачи из Redis."""
        for key in self.store.keys("cron:*"):
            raw = self.store.get(key)
            if not raw:
                continue
            try:
                data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
                name = key.split("cron:", 1)[1]
                event = data["event"]
                interval = data["interval"]
                args = data.get("args", [])
                kwargs = data.get("kwargs", {})
                job = self.scheduler.every(interval).seconds.do(
                    handle_event, event, *args, **kwargs
                )
                self.jobs[name] = job
                logging.info("[cron] восстановлена задача %s", name)
            except Exception as exc:  # pragma: no cover - restore best effort
                logging.warning("[cron] ошибка восстановления %s: %s", key, exc)

    def add_job(self, name: str, event: str, interval: int, *args: Any, **kwargs: Any) -> None:
        """Добавить задачу и сохранить её в Redis."""
        job = self.scheduler.every(interval).seconds.do(handle_event, event, *args, **kwargs)
        self.jobs[name] = job
        if self.store is not None:
            payload = json.dumps({"event": event, "interval": interval, "args": args, "kwargs": kwargs})
            self.store.set(f"cron:{name}", payload, ttl=0)
        logging.info("[cron] добавлена задача %s (%s сек)", name, interval)

    def remove_job(self, name: str) -> None:
        job = self.jobs.pop(name, None)
        if job is not None:
            self.scheduler.cancel_job(job)
        if self.store is not None:
            self.store.delete(f"cron:{name}")
        logging.info("[cron] удалена задача %s", name)

    def list_jobs(self) -> Dict[str, Any]:
        """Вернуть словарь запланированных задач."""
        return dict(self.jobs)

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
    cron.add_job("heartbeat", "OUTGOING_TO_TELEGRAM", 60, "cron alive")
    cron.run_forever()