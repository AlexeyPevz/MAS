# Примеры использования

Ниже показано несколько типовых сценариев работы с Root‑MAS. Перед запуском убедитесь, что установлены зависимости:

```bash
pip install -r requirements.txt
```

## Запуск полной системы

```bash
# Быстрый запуск всей системы
make install && make start

# Или через production launcher
python production_launcher.py
```

Система запустится со следующими компонентами:
- 12 интеллектуальных агентов
- RESTful API на порту 8080
- Telegram бот (если настроен TELEGRAM_BOT_TOKEN)
- Prometheus метрики на порту 9000
- Интерактивная консоль

## Взаимодействие через API

```bash
# Отправка сообщения
curl -X POST http://localhost:8080/api/v1/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Создай план разработки мобильного приложения"}'

# Проверка статуса
curl http://localhost:8080/api/v1/status

# Создание задачи для конкретного агента
curl -X POST http://localhost:8080/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Исследовать тренды в области ИИ", "agent": "researcher"}'
```

## Взаимодействие через Telegram

1. Создайте бота через @BotFather в Telegram
2. Установите токен в переменной окружения:
   ```bash
   export TELEGRAM_BOT_TOKEN="ваш_токен"
   ```
3. Запустите систему и найдите вашего бота в Telegram
4. Используйте команды:
   - `/start` - начало работы
   - `/help` - справка
   - `/status` - статус системы

## Интерактивная консоль

При запуске через `production_launcher.py` доступна интерактивная консоль:

```
1. Отправить сообщение
2. Статус системы
3. Статистика агентов
4. Создать задачу
5. Выход
```

## Генерация n8n‑workflow

```bash
python examples/workflow_demo.py
```

Скрипт создаст черновик workflow в n8n и активирует его при наличии `N8N_URL` и `N8N_API_KEY` в переменных окружения.

## Запрос web‑приложения через GPT‑Pilot

```bash
python examples/webapp_demo.py
```

После запуска будет отправлена спецификация приложения в GPT‑Pilot, а затем запрошен статус задания.

Более подробные примеры смотрите в директории [`examples/`](../examples).
