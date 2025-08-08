# Root-MAS: Multi-Agent System Platform 🤖

[![Python](https://img.shields.io/badge/python-3.9--3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.5.1+-orange.svg)](https://github.com/microsoft/autogen)

Платформа для создания мульти-агентных систем на базе AutoGen v0.4+ с готовой инфраструктурой.

## 🚀 Быстрый старт

### Установка и запуск одной командой:

```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/root-mas.git
cd root-mas

# Запустите автоматическую установку
python install_and_run.py
```

### Добавьте API ключ:
Откройте созданный `.env` файл и добавьте ваш ключ:
```
OPENROUTER_API_KEY=ваш-ключ-здесь
```

**Готово!** Система запущена на http://localhost:8000

## 📋 Возможности

- **12+ готовых агентов** для различных задач
- **RESTful API** с WebSocket поддержкой
- **PWA интерфейс** на `/pwa` (+ редирект с `/app`)
- **Telegram бот** (при наличии `TELEGRAM_BOT_TOKEN`)
- **Prometheus метрики** на `/metrics` и дашборд‑метрики на `/api/v1/metrics/dashboard`
- **Studio Logger интеграция**: логи пишутся в `logs/studio.jsonl` и могут быть отправлены на внешний приёмник
- **Автоматическая установка** всех зависимостей
- **Docker поддержка** для production

## 🛠️ Требования

- Python 3.9-3.13
- 4GB RAM
- API ключ от [OpenRouter](https://openrouter.ai/keys)

## 📁 Структура проекта

```
root-mas/
├── agents/         # Реализации агентов
├── api/            # REST API сервер
├── config/         # Конфигурации системы
├── prompts/        # Промпты для агентов
├── tools/          # Вспомогательные модули
└── examples/       # Примеры использования
```

## 🔧 Команды

```bash
# Проверка системы
python quick_test.py

# Последующие запуски
./start.sh          # Linux/Mac
start.bat           # Windows
python run_system.py # Универсальный

# Остановка
Ctrl+C
```

## 📖 Документация

- [Quick Start Guide](QUICK_START.md) - Подробное руководство
- [API Documentation](http://localhost:8000/docs) - Swagger UI
- [Observability](docs/observability.md) - метрики и мониторинг
- [Migration from v0.2](docs/migration/) - Для обновления с старой версии

### Примечание по AutoGen Studio
- Проект содержит `tools/studio_logger.py` — он пишет логи в `logs/studio.jsonl` и может отправлять их на внешний приёмник по адресу `${AUTOGEN_STUDIO_URL}/api/v1/logs/upload`.
- Локальная визуализация присутствует в PWA разделе Studio.

## 🤝 Вклад в проект

Мы приветствуем контрибуции! См. [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

**Нужна помощь?** Создайте [Issue](https://github.com/yourusername/root-mas/issues) или присоединяйтесь к [обсуждениям](https://github.com/yourusername/root-mas/discussions).
