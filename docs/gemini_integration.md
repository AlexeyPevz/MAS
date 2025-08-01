# Интеграция Gemini CLI в Multi-Agent System

## Обзор

Gemini CLI - это открытый AI-агент от Google, который приносит мощь Gemini 2.5 Pro прямо в терминал разработчика. Интеграция Gemini CLI в MAC систему предоставляет уникальные возможности для работы с кодом, исследований и автоматизации.

## Ключевые преимущества

### 1. **Огромный контекст (1M токенов)**
- Анализ целых кодовых баз за один запрос
- Работа с большими документами и спецификациями
- Сохранение контекста в длительных диалогах

### 2. **Бесплатный доступ с щедрыми лимитами**
- 60 запросов в минуту
- 1000 запросов в день
- Доступ к Gemini 2.5 Pro бесплатно

### 3. **Интеграция с Google Search**
- Актуальная информация о технологиях
- Исследование новых подходов
- Проверка фактов в реальном времени

### 4. **Локальное выполнение**
- Прямой доступ к файловой системе
- Выполнение команд в терминале
- Интерактивная отладка

## Архитектура интеграции

```
┌─────────────────────┐
│   MAC System        │
├─────────────────────┤
│                     │
│  ┌───────────────┐  │     ┌──────────────┐
│  │ Gemini Tools  │──┼────►│  Gemini CLI  │
│  └───────────────┘  │     │  (Terminal)  │
│                     │     └──────┬───────┘
│  ┌───────────────┐  │            │
│  │Gemini Assistant│  │            ▼
│  └───────────────┘  │     ┌──────────────┐
│                     │     │ Gemini 2.5   │
│  ┌───────────────┐  │     │    Pro       │
│  │ Other Agents  │  │     └──────────────┘
│  │ (with tools)  │  │
│  └───────────────┘  │
│                     │
└─────────────────────┘
```

## Установка и настройка

### 1. Установка Gemini CLI

```bash
# Установка через npm
npm install -g @google/gemini-cli

# Проверка установки
gemini --version
```

### 2. Настройка аутентификации

#### Вариант A: Бесплатный доступ через Google аккаунт
```bash
# Войти через Google аккаунт
gemini auth login
```

#### Вариант B: Использование API ключа
```bash
# Установить переменную окружения
export GEMINI_API_KEY="your-api-key-here"

# Или добавить в .env файл
echo "GEMINI_API_KEY=your-api-key-here" >> .env
```

### 3. Интеграция в MAC систему

Интеграция уже выполнена и включает:

1. **`tools/gemini_cli.py`** - Обертка для работы с Gemini CLI
2. **`tools/gemini_tool.py`** - Инструменты для агентов
3. **`agents/gemini_assistant.py`** - Специализированный агент
4. **`config/llm_tiers.yaml`** - Конфигурация моделей

## Использование

### 1. Как инструмент в существующих агентах

```python
from tools.gemini_tool import create_gemini_tools

# В конфигурации агента
tools = create_gemini_tools()

# Использование инструментов
result = tools["gemini_code_assist"]("Написать функцию для парсинга JSON")
analysis = tools["gemini_analyze_code"]("path/to/file.py", "security")
tests = tools["gemini_generate_tests"]("path/to/module.py")
```

### 2. Специализированный агент Gemini Assistant

```python
from agents.gemini_assistant import create_gemini_assistant

# Создание агента
gemini_agent = create_gemini_assistant()

# Агент автоматически получает доступ ко всем Gemini инструментам
# и оптимизирован для работы с большими контекстами
```

### 3. Прямое использование CLI

```python
from tools.gemini_cli import get_gemini_cli

gemini = get_gemini_cli()

# Выполнение запроса
result = await gemini.execute("Explain quantum computing")

# Анализ кода
analysis = await gemini.analyze_code("app.py", "performance")

# Исследование с Google Search
research = await gemini.research("Latest AI developments 2025")
```

## Примеры использования в MAC

### 1. Agent-Builder использует Gemini для генерации кода

```python
# Agent-Builder может использовать Gemini для создания новых агентов
gemini_code_assist("Create a new agent class for monitoring system performance")
```

### 2. Researcher дополняет свои возможности

```python
# Researcher может использовать Gemini для актуальных данных
gemini_research("Current best practices for microservices architecture")
```

### 3. WebApp-Builder генерирует компоненты

```python
# WebApp-Builder использует Gemini для создания UI компонентов
gemini_code_assist("Create a React component for real-time chat with TypeScript")
```

### 4. Fact-Checker проверяет информацию

```python
# Fact-Checker использует Google Search через Gemini
gemini_query("Verify: Python 3.13 release date and new features")
```

## Лучшие практики

### 1. Оптимизация использования контекста

- Используйте большой контекст Gemini для анализа связанных файлов
- Передавайте весь проект для архитектурных решений
- Сохраняйте историю для длительных задач

### 2. Комбинирование с другими моделями

- Используйте Gemini для сложных задач требующих большого контекста
- Переключайтесь на более дешевые модели для простых операций
- Используйте каскад моделей через Model-Selector

### 3. Безопасность

- Не передавайте чувствительные данные в Gemini
- Используйте локальное выполнение с осторожностью
- Проверяйте сгенерированный код перед выполнением

## Мониторинг и отладка

### Логирование

Все вызовы Gemini логируются через стандартную систему:

```python
import logging
logging.getLogger("tools.gemini_cli").setLevel(logging.DEBUG)
```

### Метрики

Использование Gemini отслеживается через Budget Manager:
- Количество запросов
- Использованные токены
- Время выполнения

## Расширение функциональности

### Добавление новых инструментов

```python
# В tools/gemini_tool.py
def gemini_custom_tool(params):
    """Ваш кастомный инструмент."""
    result = asyncio.run(gemini.execute(f"Custom prompt: {params}"))
    return result["response"] if result["success"] else f"Error: {result['error']}"
```

### Создание специализированных промптов

```python
# В tools/gemini_cli.py
async def specialized_analysis(self, code: str, requirements: str):
    """Специализированный анализ с кастомным промптом."""
    prompt = f"""
    Analyze this code against these requirements:
    Code: {code}
    Requirements: {requirements}
    Provide detailed compliance report.
    """
    return await self.execute(prompt)
```

## Troubleshooting

### Проблема: Gemini CLI не найден
```bash
# Проверить установку
which gemini

# Переустановить
npm uninstall -g @google/gemini-cli
npm install -g @google/gemini-cli
```

### Проблема: Ошибка аутентификации
```bash
# Проверить API ключ
echo $GEMINI_API_KEY

# Или повторно войти
gemini auth login
```

### Проблема: Превышен лимит запросов
- Используйте Budget Manager для контроля
- Переключитесь на другую модель временно
- Подождите сброса лимита (ежедневно)

## Заключение

Интеграция Gemini CLI в MAC систему предоставляет мощный инструмент для:
- Работы с большими кодовыми базами
- Получения актуальной информации
- Генерации качественного кода
- Автоматизации сложных задач

Используйте Gemini CLI как дополнение к существующим возможностям системы, выбирая его для задач, где важен большой контекст или актуальная информация.