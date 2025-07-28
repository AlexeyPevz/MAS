# Мониторинг и метрики

Этот документ описывает базовую настройку Prometheus и Grafana для Root‑MAS.

## Сбор метрик

Модуль `tools/observability.py` запускает HTTP‑сервер на порту `9000` и
экспортирует несколько метрик:

- `mas_requests_total` – количество запросов к LLM;
- `mas_tokens_total` – число использованных токенов;
- `mas_errors_total` – число ошибок обработки;
- `mas_task_seconds` – длительность выполнения задач;
- `mas_response_seconds` – время ответа модели.

Функции `record_request`, `record_tokens`, `record_error`,
`observe_duration` и `observe_response_time` можно вызывать в агентах
или коллбеках для учёта событий.

## Docker Compose

В директории [`deploy/internal`](../deploy/internal) добавлены сервисы
Prometheus и Grafana. Файл `prometheus.yml` настроен на сбор метрик с
контейнера `autogen`:

```yaml
scrape_configs:
  - job_name: mas
    static_configs:
      - targets: ['autogen:9000']
```

Запустите сервисы:

```bash
cd deploy/internal
docker compose up -d
```

Prometheus будет доступен на <http://localhost:9090>, а Grafana – на
<http://localhost:3000>. Добавьте источник данных Prometheus в Grafana и
создайте дашборд с графиками по токенам, количеству запросов и времени
ответа. Для оповещений можно настроить alert‑rules в Prometheus или
использовать стандартные возможности Grafana.
