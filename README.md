# Root-MAS: Multi-Agent System Platform 🤖

[![Python](https://img.shields.io/badge/python-3.9--3.13-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![AutoGen](https://img.shields.io/badge/AutoGen-0.9+-orange.svg)](https://github.com/microsoft/autogen)

**Root-MAS** - самообучающаяся, саморасширяющаяся и проактивная мульти-агентная система на базе AutoGen v0.9+.

## 🚀 Быстрый старт

### Вариант 1: Автоматическая установка (рекомендуется)

```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/root-mas.git
cd root-mas

# Запустите quickstart скрипт
chmod +x quickstart.sh
./quickstart.sh
```

### Вариант 2: Ручная установка

```bash
# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Скопируйте и настройте .env файл
cp .env.example .env
# Отредактируйте .env и добавьте OPENAI_API_KEY
```

## 🔑 Конфигурация

Обязательные переменные в `.env`:
```env
OPENAI_API_KEY=sk-...          # Ваш OpenAI API ключ
```

Опциональные:
```env
TELEGRAM_BOT_TOKEN=...         # Для Telegram интеграции
REDIS_HOST=localhost           # Redis для памяти
POSTGRES_HOST=localhost        # PostgreSQL для персистентности
N8N_API_URL=http://localhost:5678  # n8n для автоматизации
GPT_PILOT_URL=http://localhost:7681  # GPT-Pilot для генерации приложений
```

## 🎯 Способы запуска

### Основные команды:

```bash
# Проверка системы
python3 check_system.py

# API сервер (основной способ)
./quickstart.sh api
# или напрямую
python3 api/main.py

# Telegram бот
./quickstart.sh telegram

# Полная система
./quickstart.sh all

# Тестовый запуск
./quickstart.sh test
```

### Альтернативные способы (для обратной совместимости):

```bash
python3 run_system.py         # Запуск через supervisor
python3 install_and_run.py    # Первичная установка с GUI
```

## 📋 Ключевые возможности

### 🧠 Интеллектуальные функции
- **Саморефлексия** - агенты анализируют свою производительность
- **Q-learning** - обучение с подкреплением на основе опыта
- **Knowledge Graph** - семантическое понимание связей
- **A/B тестирование** - автоматическая оптимизация промптов
- **Федеративное обучение** - обмен знаниями между экземплярами

### 🛠️ Технические возможности
- **16+ специализированных агентов** для различных задач
- **Multi-level память** - Redis, ChromaDB, PostgreSQL
- **RESTful API** с WebSocket и rate limiting
- **PWA интерфейс** с визуализацией workflows
- **Telegram бот** с голосовой поддержкой
- **Prometheus метрики** и мониторинг
- **Event Sourcing** для полного аудита
- **Каскадная смена LLM** от дешевых к премиум моделям

### 🔗 Интеграции
- **n8n** - создание бизнес-процессов
- **GPT-Pilot** - генерация веб-приложений
- **MultiTool** - универсальный API gateway
- **AutoGen Studio** - визуализация и управление

## 📁 Структура проекта

```
root-mas/
├── agents/           # Агенты системы
│   ├── base.py      # Базовый класс с расширенными возможностями
│   ├── core_agents.py # Основные агенты
│   └── specialized_agents.py # Специализированные агенты
├── api/             # REST API сервер
│   ├── main.py      # FastAPI приложение
│   └── security.py  # JWT, RBAC, rate limiting
├── config/          # Конфигурации
│   ├── agents.yaml  # Конфигурация агентов и памяти
│   ├── llm_tiers.yaml # Каскады моделей
│   └── proactive_mode.yaml # Проактивность
├── memory/          # Системы памяти
│   ├── redis_store.py    # Краткосрочная память
│   ├── chroma_store.py   # Векторная БД
│   └── postgres_store.py # Персистентное хранилище
├── prompts/         # Системные и task-specific промпты
│   └── agents/*/    # Промпты для каждого агента
├── tools/           # Расширенные инструменты
│   ├── smart_groupchat.py # Оркестрация агентов
│   ├── quality_metrics.py # Метрики качества
│   ├── learning_loop.py   # Q-learning система
│   ├── knowledge_graph.py # Граф знаний
│   ├── ab_testing.py      # A/B тестирование
│   ├── federated_learning.py # Федеративное обучение
│   ├── event_sourcing.py  # Event sourcing
│   └── error_handler.py   # Централизованная обработка ошибок
├── pwa/             # Progressive Web App
└── data/            # Данные системы (создается автоматически)
```

## 🔧 API Endpoints

- `POST /api/v1/chat` - Основной чат endpoint
- `GET /api/v1/agents` - Статус агентов
- `GET /api/v1/metrics/dashboard` - Метрики системы
- `GET /api/v1/federation/status` - Статус федерации
- `GET /docs` - Swagger UI документация
- `GET /pwa` - Web интерфейс

## 📊 Мониторинг

- **Prometheus метрики**: http://localhost:8000/metrics
- **PWA Dashboard**: http://localhost:8000/pwa
- **API документация**: http://localhost:8000/docs
- **Логи**: `logs/` директория

## 🚀 Production Deployment

### Docker (рекомендуется)
```bash
docker-compose up -d
```

### Systemd Service
```bash
sudo cp deployment/root-mas.service /etc/systemd/system/
sudo systemctl enable root-mas
sudo systemctl start root-mas
```

## 🛡️ Безопасность

- JWT аутентификация с персистентным SECRET_KEY
- Role-Based Access Control (RBAC)
- Rate limiting на всех endpoints
- Анонимизация данных в федеративном обучении
- Цифровые подписи для обмена знаниями

## 🤝 Коммерческое использование

Root-MAS идеально подходит для:
- **SaaS платформ** - AI ассистенты для бизнеса
- **Enterprise решений** - автоматизация процессов
- **Стартапов** - быстрое прототипирование AI продуктов
- **Консалтинга** - персональные AI помощники

Каждый экземпляр эволюционирует независимо, адаптируясь под конкретные задачи владельца.

## 📖 Дополнительная документация

- [Архитектура системы](docs/architecture.md)
- [Руководство по агентам](docs/agents_guide.md)
- [Настройка памяти](docs/memory_setup.md)
- [Федеративное обучение](docs/federation.md)
- [API Reference](docs/api_reference.md)

## 🤝 Вклад в проект

Мы приветствуем контрибуции! См. [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

---

**Нужна помощь?** 
- Создайте [Issue](https://github.com/yourusername/root-mas/issues)
- Telegram: @your_support_bot
- Email: support@root-mas.ai
