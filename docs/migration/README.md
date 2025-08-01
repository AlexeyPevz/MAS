# Техническая документация по миграции на AutoGen v0.4+

## Обзор изменений

Проект обновлен с AutoGen v0.2 (pyautogen) на v0.4+ (autogen-agentchat).

### Основные изменения:
- `pyautogen>=0.2.32` → `autogen-agentchat>=0.5.1` + `autogen-ext[openai]>=0.5.5`
- `ConversableAgent` → `AssistantAgent`
- `llm_config` → `model_client`
- Добавлена поддержка асинхронности

### Обратная совместимость:
- Метод `generate_reply()` продолжает работать через адаптер
- Старый формат сообщений автоматически конвертируется
- Все существующие агенты работают без изменений

## Измененные файлы

### agents/base.py
```python
# Было:
from autogen.agentchat import ConversableAgent
class BaseAgent(ConversableAgent):
    def __init__(self, name, llm_config, ...):

# Стало:
from autogen_agentchat.agents import AssistantAgent
class BaseAgent(AssistantAgent):
    def __init__(self, name, model_client, ...):
```

### Ключевые добавления:
- Асинхронный метод `generate_reply_async()`
- Конвертация `llm_config` в `OpenAIChatCompletionClient`
- Обработка ошибок с fallback

## Новые возможности (опционально)

1. **Асинхронная архитектура**
   ```python
   response = await agent.on_messages(messages, cancellation_token)
   ```

2. **Потоковая обработка**
   ```python
   stream = team.run_stream(task="...")
   await Console(stream)
   ```

3. **Прямая работа с инструментами**
   ```python
   assistant = AssistantAgent(tools=[my_tool])
   ```

## Дополнительные ресурсы

- [Официальное руководство по миграции](https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/migration-guide.html)
- [Примеры использования](../../examples/autogen_v04_example.py)