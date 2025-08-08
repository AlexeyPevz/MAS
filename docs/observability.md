# Мониторинг и метрики

Этот документ описывает базовую настройку Prometheus и Grafana для Root‑MAS.

## Сбор метрик

Есть два варианта экспорта метрик:

1) Через встроенный эндпоинт FastAPI:
   - `GET /metrics` — отдаёт метрики в формате Prometheus, если установлен `prometheus_client`.
   - Удобно для единичного сервиса; Prometheus может скрапить сам API.

2) Через отдельный HTTP‑сервер из `tools/observability.py` (заготовка):
   - `start_metrics_server(port=9000)` поднимает экспортер на указанном порту.
   - Метрики: `mas_requests_total`, `mas_tokens_total`, `mas_errors_total`, `mas_task_seconds`, `mas_response_seconds`.
   - Вызовы `record_request`, `record_tokens`, `record_error`, `observe_duration`, `observe_response_time` — добавляйте в ключевые пути агентов/оркестрации.

## Prometheus

Пример scrape-конфига для встроенного эндпоинта `/metrics` (API на 8000 порту):

```yaml
scrape_configs:
  - job_name: mas_api
    metrics_path: /metrics
    static_configs:
      - targets: ['localhost:8000']
```

Пример scrape-конфига для отдельного экспортера на порту 9000:

```yaml
scrape_configs:
  - job_name: mas_exporter
    static_configs:
      - targets: ['localhost:9000']
```

## Docker Compose

В директории [`deploy/internal`](../deploy/internal) добавлены сервисы Prometheus и Grafana. Файл `prometheus.yml` можно
настроить на сбор метрик либо с API (`:8000/metrics`), либо с экспортера (`:9000`).

Запуск:

```bash
cd deploy/internal
docker compose up -d
```

Prometheus: <http://localhost:9090>, Grafana: <http://localhost:3000>.
Добавьте Prometheus в Grafana и создайте дашборд по токенам/запросам/времени ответа. Для оповещений используйте alert rules или Grafana Alerting.
