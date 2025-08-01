# 🚀 Root-MAS: Запуск одной командой

## Самый быстрый старт (3 шага)

### Шаг 1: Клонирование
```bash
git clone https://github.com/yourusername/root-mas.git
cd root-mas
```

### Шаг 2: Запуск установщика
```bash
# Универсальный способ (любая ОС с Python 3.9+)
python install_and_run.py

# ИЛИ для Linux/Mac
./setup.sh
```

### Шаг 3: Добавьте API ключ
Когда установщик создаст `.env` файл, откройте его и добавьте ваш ключ:
```
OPENROUTER_API_KEY=ваш-настоящий-ключ-здесь
```

**ВСЁ! Система запустится автоматически!** 🎉

---

## Что делает установщик автоматически:

### ✅ Проверяет окружение:
- Python версию (нужен 3.9-3.13)
- Удаляет старые версии AutoGen если есть
- Проверяет наличие pip

### ✅ Устанавливает всё необходимое:
- AutoGen v0.4+ (новейшая версия)
- Все зависимости из requirements.txt
- Создает виртуальное окружение (для setup.sh)

### ✅ Настраивает конфигурацию:
- Создает .env из шаблона
- Проверяет API ключи
- Создает скрипты быстрого запуска

### ✅ Запускает систему:
- API сервер на http://localhost:8000
- Документация на http://localhost:8000/docs
- Telegram бот (если настроен)

---

## Проверка системы

В любой момент можете проверить состояние:
```bash
python quick_test.py
```

Этот скрипт покажет:
- ✅ Версию Python
- ✅ Наличие .env файла
- ✅ Установленные пакеты
- ✅ Структуру проекта
- ✅ Работоспособность агентов

---

## Последующие запуски

После первой установки используйте быстрые скрипты:

### Linux/Mac:
```bash
./start.sh
```

### Windows:
```bash
start.bat
```

### Универсальный:
```bash
python run_system.py
```

---

## Решение проблем

### "Python не найден"
- Установите Python 3.9-3.13 с python.org
- Для Linux: `sudo apt install python3.11`
- Для Mac: `brew install python@3.11`

### "AutoGen не устанавливается"
```bash
pip uninstall -y pyautogen
pip install --upgrade pip
pip install autogen-agentchat>=0.5.1 autogen-ext[openai]>=0.5.5
```

### "API ключ не работает"
1. Получите ключ на https://openrouter.ai/keys
2. Добавьте в .env: `OPENROUTER_API_KEY=sk-or-v1-ваш-ключ`
3. Перезапустите систему

### "Агенты не отвечают"
- Проверьте логи: `tail -f logs/*.log`
- Запустите тест: `python test_autogen_v04.py`
- Система использует fallback режим автоматически

---

## Дополнительные возможности

### Telegram бот
Добавьте в .env:
```
TELEGRAM_BOT_TOKEN=ваш-токен-от-BotFather
```

### Docker режим
```bash
docker-compose up -d
```

### Режим разработки
```bash
ENVIRONMENT=development python run_system.py
```

---

## Полезные команды

```bash
# Проверка статуса
python quick_test.py

# Просмотр логов
tail -f logs/*.log

# Остановка системы
Ctrl+C

# Очистка логов
python cleanup_logs.py

# Обновление зависимостей
pip install -r requirements.txt --upgrade
```

---

**Готово к работе!** Система запускается одной командой и работает из коробки.

Нужна помощь? Смотрите:
- `MIGRATION_GUIDE.md` - детали миграции на AutoGen v0.4
- `AUTOGEN_V04_README.md` - новые возможности
- `examples/` - примеры использования