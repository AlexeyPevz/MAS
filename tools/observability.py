"""
observability.py
================

Заготовка для интеграции наблюдаемости (Prometheus, Grafana). Здесь
можно собирать метрики о количестве токенов, времени выполнения
задач, количестве вызовов LLM и т. д. Реализация может основываться
на библиотеке `prometheus_client`.
"""

try:
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore
except ImportError:
    # Если библиотека не установлена, определяем заглушки
    Counter = Gauge = Histogram = None  # type: ignore

# Пример базовых метрик
if Counter and Histogram:
    tokens_counter = Counter(
        "mas_tokens_total",
        "Общее количество использованных токенов",
        ["agent"],
    )
    task_duration = Histogram(
        "mas_task_seconds",
        "Время выполнения задач",
        ["agent"],
    )


def record_tokens(agent: str, amount: int) -> None:
    """Добавить количество токенов в счётчик."""
    if Counter:
        tokens_counter.labels(agent=agent).inc(amount)


def observe_duration(agent: str, seconds: float) -> None:
    """Записать длительность выполнения задачи."""
    if Histogram:
        task_duration.labels(agent=agent).observe(seconds)
