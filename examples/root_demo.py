"""
demo.py
=======

Пример использования различных модулей Root MAS. Этот скрипт демонстрирует,
как вызвать исследовательского агента, проверить источники, сгенерировать
workflow для n8n, сделать вызов внешнего API через MultiTool, а также
зарегистрировать расход токенов. Скрипт предназначен для ознакомления и
не требует запуска AutoGen.
"""

from tools.researcher import web_search
from tools.fact_checker import validate_sources
from tools.wf_builder import generate_n8n_json
from tools.multitool import call_api
from tools.observability import record_tokens


def main() -> None:
    # Исследование
    query = "Multi-agent systems AutoGen"
    results = web_search(query, max_results=3)
    print("\n--- Research Results ---")
    for res in results:
        print(res)

    # Проверка источников
    is_valid = validate_sources(results)
    print(f"\nSources valid: {is_valid}")

    # Генерация workflow
    spec = "Получать RSS-ленты из блога и отправлять новые посты в Telegram"
    wf_json = generate_n8n_json(spec)
    print("\n--- Generated n8n workflow ---")
    print(wf_json)

    # Вызов внешнего API (заглушка)
    api_response = call_api("weather", {"city": "Moscow"})
    print("\n--- External API response ---")
    print(api_response)

    # Запись расхода токенов
    record_tokens("demo", amount=123)
    print("\nTokens recorded: 123 for agent 'demo'")


if __name__ == "__main__":
    main()