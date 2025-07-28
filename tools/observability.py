"""
observability.py
================

Заготовка для интеграции наблюдаемости (Prometheus, Grafana). Здесь
можно собирать метрики о количестве токенов, времени выполнения
задач, количестве вызовов LLM и т. д. Реализация может основываться
на библиотеке `prometheus_client`.
"""

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        start_http_server,
    )  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    # Если библиотека не установлена, определяем заглушки
    Counter = Gauge = Histogram = None  # type: ignore

    def start_http_server(*_args: int, **_kwargs: int) -> None:  # type: ignore
        print("[observability] prometheus_client not installed")

# Пример базовых метрик
if Counter and Histogram:
    tokens_counter = Counter(
        "mas_tokens_total",
        "Общее количество использованных токенов",
        ["agent"],
    )
    requests_counter = Counter(
        "mas_requests_total",
        "Количество запросов к LLM",
        ["agent"],
    )
    errors_counter = Counter(
        "mas_errors_total",
        "Количество ошибок при обработке запросов",
        ["agent"],
    )
    task_duration = Histogram(
        "mas_task_seconds",
        "Время выполнения задач",
        ["agent"],
    )
    response_time = Histogram(
        "mas_response_seconds",
        "Время ответа LLM",
        ["agent"],
    )


def start_metrics_server(port: int = 9000) -> None:
    """Start HTTP server that exposes Prometheus metrics."""

    if start_http_server:
        start_http_server(port)
        print(f"[observability] Prometheus metrics available on port {port}")


def record_tokens(agent: str, amount: int) -> None:
    """Добавить количество токенов в счётчик."""
    if Counter:
        tokens_counter.labels(agent=agent).inc(amount)


def record_request(agent: str) -> None:
    """Увеличить счётчик запросов."""
    if Counter:
        requests_counter.labels(agent=agent).inc()


def record_error(agent: str) -> None:
    """Увеличить счётчик ошибок."""
    if Counter:
        errors_counter.labels(agent=agent).inc()


def observe_duration(agent: str, seconds: float) -> None:
    """Записать длительность выполнения задачи."""
    if Histogram:
        task_duration.labels(agent=agent).observe(seconds)


def observe_response_time(agent: str, seconds: float) -> None:
    """Записать время ответа LLM."""
    if Histogram:
        response_time.labels(agent=agent).observe(seconds)


# -------------------------------------------------------------
# Convenience utilities
# -------------------------------------------------------------

import time
from functools import wraps
from typing import Callable, ParamSpec, TypeVar, Any

P = ParamSpec("P")
R = TypeVar("R")


def observe_llm_call(agent: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that records basic metrics for an LLM call.

    The wrapped function *should* either:

    1. Accept keyword argument ``tokens`` with the number of output tokens, **or**
    2. Return an object (dict, attr) with attribute/field ``tokens``.

    If none of these are available, only request/error/duration metrics are
    recorded.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:  # type: ignore[misc]
            start = time.perf_counter()
            record_request(agent)
            try:
                result = func(*args, **kwargs)
            except Exception:
                record_error(agent)
                raise
            finally:
                observe_duration(agent, time.perf_counter() - start)

            # Записываем токены, если доступны.
            tokens_val: Any | None = None
            if "tokens" in kwargs:
                tokens_val = kwargs.get("tokens")
            elif isinstance(result, dict) and "tokens" in result:
                tokens_val = result.get("tokens")

            if isinstance(tokens_val, int):
                record_tokens(agent, tokens_val)

            return result

        return wrapper

    return decorator

