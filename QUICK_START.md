# 🚀 Root-MAS Quick Start Guide

## Быстрый запуск за 2 минуты

### 1. Клонирование и настройка

```bash
# Клонируем репозиторий
git clone <repo-url> root-mas
cd root-mas

# Копируем файл окружения
cp .env.example .env

# Редактируем .env и добавляем OPENROUTER_API_KEY
nano .env  # или используйте любой редактор
```

### 2. Запуск системы

```bash
# Вариант 1: Через Make (рекомендуется)
make install && make start

# Вариант 2: Через deploy.sh
./deploy.sh install
./deploy.sh start

# Вариант 3: Вручную
pip install -r requirements.txt
python production_launcher.py
```

### 3. Готово! 🎉

Ваша MAS система запущена со следующими компонентами:

- ✅ **12 интеллектуальных агентов**
- ✅ **RESTful API** на http://localhost:8080
- ✅ **Telegram бот** (если настроен токен)
- ✅ **Prometheus метрики** на http://localhost:9000
- ✅ **Интерактивная консоль**

## 📱 Использование

### Через API

```bash
# Отправить сообщение
curl -X POST http://localhost:8080/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Создай план проекта"}'

# Проверить статус
curl http://localhost:8080/api/v1/status
```

### Через Telegram

1. Создайте бота через @BotFather
2. Добавьте токен в .env: `TELEGRAM_BOT_TOKEN=ваш_токен`
3. Перезапустите систему: `make restart`
4. Найдите вашего бота в Telegram

### Через консоль

При запуске выберите опцию:
- `1` - Отправить сообщение
- `2` - Статус системы
- `3` - Статистика агентов
- `4` - Создать задачу
- `5` - Выход

## 🛠️ Управление

```bash
make status    # Проверить статус
make logs      # Посмотреть логи
make restart   # Перезапустить
make stop      # Остановить
make clean     # Очистить
```

## 📊 Мониторинг

- **API документация**: http://localhost:8080/api/v1/
- **Prometheus метрики**: http://localhost:9000/metrics
- **Логи**: `logs/mas_production.log`

## ❓ Частые вопросы

**Q: Как добавить новые LLM модели?**
A: Отредактируйте `config/llm_tiers.yaml`

**Q: Как изменить промпты агентов?**
A: Смотрите файлы в `prompts/agents/*/`

**Q: Как настроить бюджет?**
A: В .env установите `DAILY_BUDGET_LIMIT=100.0`

## 🆘 Поддержка

- Документация: [`docs/`](docs/)
- Примеры: [`examples/`](examples/)
- Issues: GitHub Issues