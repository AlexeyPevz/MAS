# 🌐 Руководство по использованию Web Installer

## 📋 Содержание
1. [Быстрый старт](#быстрый-старт)
2. [Способы запуска](#способы-запуска)
3. [Пошаговая инструкция](#пошаговая-инструкция)
4. [Обработка ошибок](#обработка-ошибок)
5. [Продвинутые возможности](#продвинутые-возможности)
6. [FAQ](#faq)

## 🚀 Быстрый старт

### Вариант 1: Запуск через Python сервер
```bash
# Перейти в папку installer
cd installer

# Запустить локальный веб-сервер
python -m http.server 5000

# Или через Python 2 (если установлен)
python -m SimpleHTTPServer 5000
```

Откройте браузер: http://localhost:5000/web_installer.html

### Вариант 2: Запуск через встроенный сервер
```bash
# Использовать специальный скрипт запуска
python installer/start_web_installer.py
```

### Вариант 3: Прямое открытие файла
```bash
# Открыть в браузере по умолчанию
# Linux/Mac
xdg-open installer/web_installer.html  # Linux
open installer/web_installer.html      # Mac

# Windows
start installer/web_installer.html
```

### Вариант 4: Через главный скрипт
```bash
# Автоматически определит и запустит веб-версию
python install.py --web
```

## 📖 Пошаговая инструкция

### Шаг 1: Выбор типа установки
![Step 1](docs/images/web_step1.png)

1. **Локальная установка** - установка на текущий компьютер
2. **Docker контейнер** - изолированная установка (требует Docker)
3. **Облачная установка** - развертывание в облаке (AWS/GCP/Azure)

**Путь установки**: по умолчанию `/home/user/ai-memory-system`, можно изменить

### Шаг 2: Выбор компонентов
![Step 2](docs/images/web_step2.png)

Обязательные компоненты:
- ✅ **Ядро системы** - всегда установлено

Опциональные:
- 📱 **Telegram Bot** - интеграция с Telegram
- 🚀 **GPT-Pilot** - создание приложений с помощью AI
- 🎬 **AutoGen Studio** - визуальный интерфейс
- 📊 **Мониторинг** - Prometheus + Grafana
- 💾 **Хранилища** - Redis + PostgreSQL + ChromaDB

### Шаг 3: Конфигурация API
![Step 3](docs/images/web_step3.png)

Обязательные ключи:
- **OpenAI API Key** или **Anthropic API Key** (минимум один)

Опциональные:
- **Telegram Bot Token** - если выбран Telegram компонент
- **Другие API ключи** - в зависимости от компонентов

🧪 **Тест API ключей** - проверяет валидность введенных ключей

### Шаг 4: Дополнительные настройки
![Step 4](docs/images/web_step4.png)

- 🚀 **Автозапуск** - запустить систему после установки
- 🖥️ **Ярлык на рабочем столе** - быстрый доступ
- 🔧 **Добавить в PATH** - запуск из командной строки
- 📊 **Аналитика** - помочь улучшить систему

### Шаг 5: Установка
![Step 5](docs/images/web_step5.png)

Нажмите "🚀 Начать установку" и следите за прогрессом:
- Прогресс бар показывает общий прогресс
- Текущий этап отображается сверху
- Лог установки показывает детали
- При ошибках появятся диалоги с решениями

## 🛡️ Обработка ошибок

### Автоматическая диагностика
Веб-инсталлятор автоматически определяет и предлагает решения для:

#### 1. Недостаточно места на диске
```javascript
⚠️ Недостаточно места на диске!
Требуется: 2 GB
Доступно: 500 MB

Варианты решения:
[Очистить кэш] [Выбрать другой диск] [Отмена]
```

#### 2. Порты заняты
```javascript
⚠️ Порт 8000 уже используется!
Процесс: python (PID: 1234)

Варианты:
[Остановить процесс] [Использовать другой порт] [Отмена]
```

#### 3. Нет интернета
```javascript
⚠️ Нет подключения к интернету!

Варианты:
[Повторить] [Офлайн установка] [Настройки прокси]
```

### Восстановление после ошибок
При возникновении ошибки:
1. Появится диалог с описанием проблемы
2. Предложены варианты решения
3. После выбора решения установка продолжится
4. Прогресс сохраняется

## 🎨 Продвинутые возможности

### 1. Сохранение конфигурации
```javascript
// Сохранить текущую конфигурацию
function saveConfig() {
    const config = {
        installType: getSelectedInstallType(),
        components: getSelectedComponents(),
        path: document.getElementById('install-path').value,
        // ... другие настройки
    };
    
    // Скачать как файл
    downloadJSON(config, 'install-config.json');
}

// Загрузить сохраненную конфигурацию
function loadConfig(file) {
    // Автозаполнение всех полей
}
```

### 2. Кастомные компоненты
Добавьте свои компоненты в `installer/web_components.json`:
```json
{
    "custom_component": {
        "name": "My Custom Component",
        "icon": "🔧",
        "description": "Мой компонент",
        "requirements": ["python>=3.8"],
        "install_script": "install_custom.sh"
    }
}
```

### 3. Темы оформления
```javascript
// Переключение темы
function toggleTheme() {
    document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', 
        document.body.classList.contains('light-theme') ? 'light' : 'dark'
    );
}
```

### 4. Интеграция с backend
Для полноценной установки подключите backend:
```javascript
// installer/web_installer_backend.py
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/api/install', methods=['POST'])
def install():
    config = request.json
    # Запуск реальной установки
    result = subprocess.run(['python', 'cli_installer.py', '--config', config])
    return jsonify({'success': result.returncode == 0})
```

### 5. WebSocket для real-time логов
```javascript
// Подключение к WebSocket для логов
const ws = new WebSocket('ws://localhost:5001/logs');

ws.onmessage = function(event) {
    addToLog(event.data);
};

ws.onerror = function(error) {
    addToLog('❌ Ошибка подключения: ' + error);
};
```

## 🔧 Настройка для production

### 1. Через Nginx
```nginx
server {
    listen 80;
    server_name installer.yourdomain.com;
    
    location / {
        root /var/www/installer;
        index web_installer.html;
    }
    
    location /api/ {
        proxy_pass http://localhost:5001;
        proxy_set_header Host $host;
    }
    
    location /ws/ {
        proxy_pass http://localhost:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 2. Docker контейнер для инсталлятора
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY installer/ ./installer/

RUN pip install flask flask-cors websocket-server

EXPOSE 5000 5001

CMD ["python", "installer/web_installer_server.py"]
```

### 3. Kubernetes deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-installer
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web-installer
  template:
    metadata:
      labels:
        app: web-installer
    spec:
      containers:
      - name: installer
        image: ai-memory-system/installer:latest
        ports:
        - containerPort: 5000
        - containerPort: 5001
```

## ❓ FAQ

### Q: Можно ли использовать веб-инсталлятор удаленно?
**A:** Да! Запустите на сервере:
```bash
python installer/start_web_installer.py --host 0.0.0.0 --port 8080
```
Затем откройте `http://server-ip:8080/web_installer.html`

### Q: Как добавить авторизацию?
**A:** Используйте встроенную поддержку:
```javascript
// В начале web_installer.html
if (!checkAuth()) {
    window.location.href = '/login.html';
}
```

### Q: Поддерживается ли мобильная версия?
**A:** Да, интерфейс адаптивный. На мобильных устройствах:
- Шаги отображаются вертикально
- Кнопки увеличены для удобства
- Поддержка жестов

### Q: Можно ли встроить в существующий сайт?
**A:** Да, через iframe:
```html
<iframe src="installer/web_installer.html" 
        width="100%" 
        height="800px"
        frameborder="0">
</iframe>
```

### Q: Как добавить свой язык?
**A:** Создайте файл перевода:
```javascript
// installer/locales/es.json
{
    "title": "Instalador del Sistema AI Memory",
    "step1.title": "Seleccionar tipo de instalación",
    // ...
}
```

### Q: Безопасно ли вводить API ключи?
**A:** Да, при условии:
- Используется HTTPS
- Ключи не логируются
- Передаются только на backend
- Хранятся в зашифрованном виде

## 🚨 Решение проблем

### Не открывается в браузере
1. Проверьте путь к файлу
2. Попробуйте другой браузер (Chrome/Firefox/Edge)
3. Отключите блокировщики скриптов

### Не работает установка
1. Проверьте консоль браузера (F12)
2. Убедитесь, что backend запущен
3. Проверьте права доступа

### Ошибки CORS
Добавьте в backend:
```python
from flask_cors import CORS
CORS(app, origins=['http://localhost:5000'])
```

### Медленная загрузка
1. Используйте CDN для библиотек
2. Включите сжатие gzip
3. Минифицируйте JS/CSS

---

💡 **Совет**: Для максимального удобства используйте веб-инсталлятор вместе с System Doctor для предварительной проверки системы!