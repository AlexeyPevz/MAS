# Руководство по миграции AutoGen v0.2 → v0.4+

## Обзор изменений

Проект был обновлен с устаревшей версии AutoGen (pyautogen 0.2.32) на новейшую версию (autogen-agentchat 0.5.1+).

### Основные изменения:

1. **Новые пакеты**:
   - `pyautogen>=0.2.32` → `autogen-agentchat>=0.5.1` + `autogen-ext[openai]>=0.5.5`
   - AutoGen теперь разделен на несколько пакетов с разными функциями

2. **Архитектурные изменения**:
   - Переход на асинхронную, событийно-ориентированную архитектуру
   - `ConversableAgent` → `AssistantAgent` 
   - `llm_config` → `model_client`
   - `generate_reply()` → `on_messages()` (асинхронный)

3. **Конфигурация моделей**:
   - Вместо `llm_config` с `config_list` теперь используется `OpenAIChatCompletionClient`
   - Прямая конфигурация клиента с параметрами модели

## Что было изменено в коде

### 1. requirements.txt
```diff
- pyautogen>=0.2.32
+ autogen-agentchat>=0.5.1
+ autogen-ext[openai]>=0.5.5
```

### 2. agents/base.py
- Импорты обновлены для новых API
- `ConversableAgent` заменен на `AssistantAgent`
- Добавлен `OpenAIChatCompletionClient` для работы с моделями
- Добавлены асинхронные методы `generate_reply_async()` для совместимости
- Конвертация старого формата `llm_config` в новый `model_client`

### 3. agents/core_agents.py
- Обновлены импорты на новые API классы
- Типы изменены с `ConversableAgent` на `AssistantAgent`

### 4. tools/callbacks.py
- Временно отключен импорт `autogen.agentchat` с TODO для будущей миграции

## Обратная совместимость

Для обеспечения работы существующего кода:
1. Добавлен метод `generate_reply()` как синхронная обертка над асинхронным `on_messages()`
2. Конвертация старого формата сообщений в новый формат `TextMessage`
3. Сохранена структура классов агентов

## Следующие шаги

1. **Полный переход на асинхронность**:
   - Обновить все вызовы агентов на асинхронные
   - Использовать `await agent.on_messages()` вместо `agent.generate_reply()`

2. **Обновление взаимодействий агентов**:
   - Заменить прямые вызовы на Teams API (RoundRobinGroupChat, SelectorGroupChat)
   - Использовать `run_stream()` для потоковой обработки

3. **Миграция инструментов**:
   - Обновить регистрацию инструментов через параметр `tools` в `AssistantAgent`
   - Убрать необходимость в UserProxy для выполнения инструментов

4. **Тестирование**:
   - Протестировать все агенты на корректную работу
   - Проверить производительность асинхронных вызовов

## Полезные ссылки

- [Официальное руководство по миграции](https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/migration-guide.html)
- [Документация AutoGen v0.4](https://microsoft.github.io/autogen/dev/)
- [Примеры использования новых API](https://github.com/microsoft/autogen/tree/main/examples)