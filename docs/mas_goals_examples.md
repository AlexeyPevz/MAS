# Примеры целей для MAS (MAS_GOAL)

Переменная `MAS_GOAL` определяет задачу, которую должна выполнить ваша мультиагентная система.

## 🤖 Проактивный AI-ассистент

```bash
# Полноценный проактивный помощник
MAS_GOAL="act as a proactive AI assistant helping with any questions and tasks"

# Фокусированные варианты
MAS_GOAL="be my coding assistant and help with development tasks"
MAS_GOAL="act as my personal productivity assistant"
MAS_GOAL="help me manage and optimize my daily workflow"
MAS_GOAL="be my research assistant and help find solutions"
MAS_GOAL="assist with project management and planning"
```

## 🔧 Тестовые цели

```bash
# Базовая проверка работоспособности
MAS_GOAL="echo"

# Тест системы агентов
MAS_GOAL="test"
```

## 📖 Анализ и документация

```bash
# Анализ документации
MAS_GOAL="summarise the README"
MAS_GOAL="analyze project documentation"
MAS_GOAL="review code comments quality"

# Анализ структуры проекта
MAS_GOAL="analyze project structure"
MAS_GOAL="identify potential security issues"
MAS_GOAL="review database schema"
```

## 🏗️ Разработка и создание

```bash
# Создание документации
MAS_GOAL="create a user manual"
MAS_GOAL="generate API documentation"
MAS_GOAL="write installation guide"

# Генерация кода и тестов
MAS_GOAL="generate test cases for user authentication"
MAS_GOAL="create unit tests for payment module"
MAS_GOAL="implement error handling patterns"
```

## 🐛 Отладка и оптимизация

```bash
# Поиск и исправление проблем
MAS_GOAL="fix critical bugs in payment module"
MAS_GOAL="optimize database queries"
MAS_GOAL="improve application performance"

# Рефакторинг
MAS_GOAL="refactor legacy code in user module"
MAS_GOAL="improve code readability"
MAS_GOAL="modernize deprecated functions"
```

## 🎯 Бизнес-задачи

```bash
# Новые функции
MAS_GOAL="implement new feature: user authentication"
MAS_GOAL="add payment integration with Stripe"
MAS_GOAL="create admin dashboard"

# Интеграции
MAS_GOAL="integrate with external API"
MAS_GOAL="setup monitoring and alerting"
MAS_GOAL="implement data backup strategy"
```

## 📊 Анализ и отчеты

```bash
# Аналитика
MAS_GOAL="analyze user behavior patterns"
MAS_GOAL="generate performance report"
MAS_GOAL="create security audit report"

# Мониторинг
MAS_GOAL="setup health checks"
MAS_GOAL="implement logging strategy"
MAS_GOAL="create error tracking system"
```

## 🎨 UI/UX задачи

```bash
# Пользовательский интерфейс
MAS_GOAL="improve user interface design"
MAS_GOAL="create responsive layout"
MAS_GOAL="implement accessibility features"

# Пользовательский опыт
MAS_GOAL="optimize user registration flow"
MAS_GOAL="improve error messages"
MAS_GOAL="create onboarding tutorial"
```

## 🔐 Безопасность

```bash
# Аудит безопасности
MAS_GOAL="perform security vulnerability scan"
MAS_GOAL="implement input validation"
MAS_GOAL="setup rate limiting"

# Защита данных
MAS_GOAL="encrypt sensitive data"
MAS_GOAL="implement secure authentication"
MAS_GOAL="setup data privacy compliance"
```

## 📈 Производительность

```bash
# Оптимизация
MAS_GOAL="optimize application startup time"
MAS_GOAL="reduce memory usage"
MAS_GOAL="improve API response time"

# Масштабирование
MAS_GOAL="implement caching strategy"
MAS_GOAL="setup load balancing"
MAS_GOAL="optimize database connections"
```

## 💡 Советы по написанию целей

1. **Будьте конкретны**: вместо "fix bugs" напишите "fix authentication timeout in login module"

2. **Указывайте контекст**: "analyze user authentication flow in the current codebase"

3. **Определяйте область**: "optimize SQL queries in the payment processing module"

4. **Используйте действия**: начинайте с глаголов (analyze, create, implement, fix, optimize)

5. **Включайте ограничения**: "create API documentation following OpenAPI 3.0 standard"

## 🚀 Как установить цель

### В .env файле:
```bash
MAS_GOAL="your goal here"
```

### Через переменную окружения:
```bash
export MAS_GOAL="analyze project structure"
```

### В Docker Compose:
```yaml
environment:
  MAS_GOAL: "create user manual"
```

### При запуске контейнера:
```bash
docker run -e MAS_GOAL="summarise the README" your-app
```