# Быстрая настройка Gemini CLI для MAC

## 🚀 Рекомендуемый способ (БЕСПЛАТНО)

### Шаг 1: Установка
```bash
# Если еще не установлен
npm install -g @google/gemini-cli
```

### Шаг 2: Аутентификация через Google аккаунт
```bash
# Запустите команду
gemini auth login

# Откроется браузер:
# 1. Войдите в ваш Google аккаунт
# 2. Разрешите доступ для Gemini CLI
# 3. Вернитесь в терминал - всё готово!
```

### Шаг 3: Проверка
```bash
# Проверим что всё работает
gemini "Hello, are you working?"

# Должен ответить что-то вроде:
# "Hello! Yes, I'm working properly. How can I help you today?"
```

## 🔑 Альтернатива: Google AI Studio

Если хотите использовать API ключ:

1. Перейдите на https://aistudio.google.com/app/apikey
2. Нажмите "Create API key" 
3. Выберите "Create API key in new project" (проект создастся автоматически)
4. Скопируйте ключ

```bash
# Добавьте в .env файл вашего проекта
echo "GEMINI_API_KEY=AIzaSy..." >> .env

# Или экспортируйте для текущей сессии
export GEMINI_API_KEY="AIzaSy..."
```

## ❓ Часто задаваемые вопросы

**Q: Нужен ли Google Cloud проект?**
A: НЕТ! Для бесплатного использования достаточно обычного Google аккаунта.

**Q: Какие лимиты при бесплатном использовании?**
A: 60 запросов/минуту и 1000 запросов/день - очень щедро!

**Q: Могу ли я использовать для production?**
A: Да, но для высоких нагрузок лучше использовать API ключ или Vertex AI.

**Q: Работает ли в России/Беларуси?**
A: Может потребоваться VPN для первичной аутентификации. После получения токена/ключа может работать и без VPN.

## 🛠️ Интеграция в MAC систему

После настройки аутентификации, ваша MAC система автоматически будет использовать Gemini CLI:

```python
# В коде ничего менять не нужно!
# tools/gemini_cli.py автоматически подхватит аутентификацию

from tools.gemini_tool import create_gemini_tools
tools = create_gemini_tools()

# Используйте как обычно
result = tools["gemini_code_review"]("file.py")
```

## 🚨 Troubleshooting

### Ошибка "Command not found: gemini"
```bash
# Проверьте установку npm
npm --version

# Переустановите Gemini CLI
npm uninstall -g @google/gemini-cli
npm install -g @google/gemini-cli

# Проверьте PATH
echo $PATH
# Должен содержать путь к npm глобальным пакетам
```

### Ошибка аутентификации
```bash
# Попробуйте выйти и войти заново
gemini auth logout
gemini auth login

# Или используйте API ключ вместо OAuth
```

### Ошибка "Rate limit exceeded"
- Подождите несколько минут
- Проверьте не используете ли вы Gemini в других приложениях
- Рассмотрите использование API ключа для увеличения лимитов

## 📞 Поддержка

- Документация: https://github.com/google-gemini/gemini-cli
- Issues: https://github.com/google-gemini/gemini-cli/issues
- Сообщество: https://discord.gg/gemini-dev