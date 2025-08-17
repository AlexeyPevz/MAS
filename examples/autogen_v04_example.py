"""
Пример использования новых API AutoGen v0.4
Демонстрирует основные изменения и новые возможности
"""

import asyncio
import os
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken


async def basic_agent_example():
    """Пример базового использования агента"""
    print("=== Пример 1: Базовый агент ===")
    
    # Создаем клиент модели (замена llm_config)
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENROUTER_API_KEY", "mock-key"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=2000
    )
    
    # Создаем агента с новым API
    assistant = AssistantAgent(
        name="assistant",
        system_message="Ты полезный помощник, который отвечает на русском языке.",
        model_client=model_client,
    )
    
    # Используем новый асинхронный метод on_messages
    cancellation_token = CancellationToken()
    response = await assistant.on_messages(
        [TextMessage(content="Привет! Расскажи мне о новых возможностях AutoGen v0.4", source="user")],
        cancellation_token
    )
    
    print(f"Ответ агента: {response.chat_message.content}")
    await model_client.close()


async def team_collaboration_example():
    """Пример командной работы агентов"""
    print("\n=== Пример 2: Командная работа ===")
    
    # Создаем клиент модели
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENROUTER_API_KEY", "mock-key"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    # Создаем агентов для команды
    writer = AssistantAgent(
        name="writer",
        description="Писатель, создающий истории",
        system_message="Ты творческий писатель. Пиши короткие истории на русском языке.",
        model_client=model_client,
    )
    
    critic = AssistantAgent(
        name="critic",
        description="Критик, оценивающий истории",
        system_message="Ты литературный критик. Давай конструктивную обратную связь. Если история хорошая, скажи 'ОДОБРЕНО'.",
        model_client=model_client,
    )
    
    # Условия завершения
    termination = TextMentionTermination("ОДОБРЕНО") | MaxMessageTermination(6)
    
    # Создаем групповой чат с новым API
    team = RoundRobinGroupChat(
        [writer, critic],
        termination_condition=termination,
        max_turns=6
    )
    
    # Запускаем задачу
    task = "Напиши короткую историю о роботе, который научился мечтать"
    result = await team.run(task=task)
    
    print(f"\nРезультат работы команды:")
    print(f"Количество сообщений: {len(result.messages)}")
    print(f"Последнее сообщение: {result.messages[-1].content}")
    
    await model_client.close()


async def tool_use_example():
    """Пример использования инструментов в v0.4"""
    print("\n=== Пример 3: Использование инструментов ===")
    
    # Определяем инструменты
    def get_weather(city: str) -> str:
        """Получить погоду в городе"""
        return f"Погода в {city}: 20°C, солнечно"
    
    def calculate(expression: str) -> str:
        """Вычислить математическое выражение"""
        try:
            import ast
            result = ast.literal_eval(expression)
            return f"Результат: {result}"
        except Exception:
            return "Ошибка вычисления"
    
    # Создаем клиент модели
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENROUTER_API_KEY", "mock-key"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    # Создаем агента с инструментами (больше не нужен UserProxy!)
    assistant = AssistantAgent(
        name="assistant",
        system_message="Ты помощник, который может узнавать погоду и выполнять вычисления.",
        model_client=model_client,
        tools=[get_weather, calculate],  # Инструменты передаются напрямую
        reflect_on_tool_use=True  # Агент будет анализировать результаты инструментов
    )
    
    # Тестируем инструменты
    messages = [
        TextMessage(content="Какая погода в Москве?", source="user"),
        TextMessage(content="Сколько будет 123 * 456?", source="user")
    ]
    
    for msg in messages:
        response = await assistant.on_messages([msg], CancellationToken())
        print(f"\nВопрос: {msg.content}")
        print(f"Ответ: {response.chat_message.content}")
    
    await model_client.close()


async def streaming_example():
    """Пример потоковой обработки сообщений"""
    print("\n=== Пример 4: Потоковая обработка ===")
    
    model_client = OpenAIChatCompletionClient(
        model="gpt-4o-mini",
        api_key=os.getenv("OPENROUTER_API_KEY", "mock-key"),
        base_url="https://openrouter.ai/api/v1"
    )
    
    assistant = AssistantAgent(
        name="assistant",
        system_message="Ты помощник, который подробно объясняет концепции.",
        model_client=model_client,
    )
    
    # Создаем простую команду для демонстрации потоковой обработки
    team = RoundRobinGroupChat([assistant], max_turns=1)
    
    # Используем run_stream для получения потока сообщений
    print("Потоковая обработка:")
    stream = team.run_stream(task="Объясни, что такое машинное обучение")
    
    # Console автоматически обрабатывает и отображает поток
    await Console(stream)
    
    await model_client.close()


# Вспомогательная функция для запуска примеров
async def main():
    """Запуск всех примеров"""
    print("🚀 Демонстрация новых возможностей AutoGen v0.4\n")
    
    try:
        # Базовый пример
        await basic_agent_example()
        
        # Командная работа
        await team_collaboration_example()
        
        # Использование инструментов
        await tool_use_example()
        
        # Потоковая обработка
        await streaming_example()
        
    except Exception as e:
        print(f"\n⚠️ Ошибка: {e}")
        print("Убедитесь, что установлены все зависимости и настроены API ключи")


if __name__ == "__main__":
    # Запускаем асинхронные примеры
    asyncio.run(main())