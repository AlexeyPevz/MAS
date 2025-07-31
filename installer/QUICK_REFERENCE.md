# 📚 Краткая шпаргалка по инсталляторам AI Memory System

## 🚀 Быстрый запуск

### 🌐 Web Installer (Браузерная версия)

```bash
# Способ 1: Через специальный скрипт (РЕКОМЕНДУЕТСЯ)
python installer/start_web_installer.py

# Способ 2: Через Python HTTP сервер
cd installer
python -m http.server 5000
# Открыть: http://localhost:5000/web_installer.html

# Способ 3: Прямое открытие
open installer/web_installer.html      # Mac
xdg-open installer/web_installer.html  # Linux
start installer/web_installer.html     # Windows

# Способ 4: Для удаленного доступа
python installer/start_web_installer.py --host 0.0.0.0 --port 8080
```

### 🖥️ GUI Installer (Оконная версия)

```bash
# Запуск GUI инсталлятора
python installer/universal_installer.py

# Или через главный скрипт
python install.py --gui
```

### 💻 CLI Installer (Консольная версия)

```bash
# Интерактивный режим
python installer/cli_installer.py

# Быстрая установка
python installer/cli_installer.py --quick

# Полностью автоматическая
python installer/cli_installer.py --quick --yes --path /opt/ai-memory
```

## 🩺 Диагностика и исправление проблем

### Проверка системы
```bash
# Полная диагностика
python installer/system_doctor.py

# Автоматическое исправление
python installer/system_doctor.py --fix

# Проверка конкретной подсистемы
python installer/system_doctor.py --check memory
python installer/system_doctor.py --check network

# Сохранение отчета
python installer/system_doctor.py --report diagnostic.json
```

## 🎯 Типичные сценарии

### 1. Первая установка
```bash
# 1. Проверка системы
python installer/system_doctor.py

# 2. Исправление проблем (если есть)
python installer/system_doctor.py --fix

# 3. Запуск инсталлятора (любого)
python installer/start_web_installer.py  # Веб-версия
# или
python install.py  # Автовыбор подходящего
```

### 2. Установка на сервер через SSH
```bash
# Вариант 1: CLI на сервере
ssh user@server
git clone <repo>
cd ai-memory-system
python installer/cli_installer.py --quick

# Вариант 2: GUI с локальной машины
python installer/universal_installer.py
# Выбрать "Удаленная установка"
# Ввести SSH данные
```

### 3. Docker установка
```bash
# Через веб-инсталлятор
python installer/start_web_installer.py
# Выбрать "Docker контейнер"

# Или напрямую
docker-compose up -d
```

### 4. Установка без интернета
```bash
# Подготовка офлайн пакетов (на машине с интернетом)
python installer/prepare_offline.py

# Установка (на целевой машине)
python installer/cli_installer.py --offline
```

## ⚡ Горячие клавиши

### Web Installer
- `Enter` - следующий шаг
- `Backspace` - предыдущий шаг
- `Ctrl+S` - сохранить конфигурацию
- `Ctrl+L` - загрузить конфигурацию

### GUI Installer
- `Tab` - переключение между элементами
- `Space` - выбор чекбокса
- `Alt+N` - следующий шаг
- `Alt+B` - предыдущий шаг

### CLI Installer
- `↑/↓` - навигация по меню
- `Space` - выбор опции
- `Enter` - подтверждение
- `Ctrl+C` - отмена

## 🆘 Решение частых проблем

### "Недостаточно места на диске"
```bash
# Автоматическая очистка
python installer/system_doctor.py --fix

# Или вручную
sudo apt-get clean  # Linux
brew cleanup        # Mac
# Удалить старые логи и кэш
```

### "Порт уже занят"
```bash
# Найти процесс
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Или автоматически
python installer/system_doctor.py --fix
```

### "Нет прав доступа"
```bash
# Установка в пользовательскую директорию
python installer/cli_installer.py --path ~/ai-memory

# Или с sudo (не рекомендуется)
sudo python install.py
```

### "Ошибка SSL/сертификата"
```bash
# Временное решение
export PYTHONHTTPSVERIFY=0
python install.py

# Или обновить сертификаты
pip install --upgrade certifi
```

## 📝 Полезные команды

### Управление установкой
```bash
# Проверить статус
systemctl status ai-memory-system  # Linux с systemd

# Запустить/остановить
python run_system.py               # Запуск
systemctl start ai-memory-system   # Через systemd

# Обновить
git pull
python installer/update_system.py

# Удалить
python installer/uninstall.py
```

### Логи и отладка
```bash
# Просмотр логов установки
tail -f installer/logs/install_*.log

# Логи системы
tail -f logs/system.log

# Включить debug режим
export DEBUG=1
python install.py
```

## 🔗 Быстрые ссылки

- 📖 [Полное руководство по Web Installer](WEB_INSTALLER_GUIDE.md)
- 🛡️ [Обработка ошибок](ADVANCED_FEATURES.md)
- 🩺 [System Doctor документация](error_handler.py)
- 📚 [Основная документация](../README.md)

---

💡 **Совет**: Начните с `python installer/system_doctor.py` для проверки готовности системы!