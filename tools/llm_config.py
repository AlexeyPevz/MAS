"""
LLM Configuration Module
Настройка конфигурации для различных LLM провайдеров
"""
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml


def load_llm_tiers() -> Dict[str, Any]:
    """Загрузка конфигурации LLM уровней"""
    config_path = Path(__file__).parent.parent / "config" / "llm_tiers.yaml"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"⚠️ Ошибка загрузки llm_tiers.yaml: {e}")
        return get_default_tiers()


def get_default_tiers() -> Dict[str, Any]:
    """Базовая конфигурация если файл недоступен"""
    return {
        "tiers": {
            "cheap": [
                {"name": "gpt-3.5-turbo", "provider": "openrouter"},
                {"name": "llama-3.1-8b-instruct", "provider": "openrouter"}
            ],
            "standard": [
                {"name": "gpt-4o-mini", "provider": "openrouter"},
                {"name": "claude-3-haiku", "provider": "openrouter"}
            ],
            "premium": [
                {"name": "gpt-4o", "provider": "openrouter"},
                {"name": "claude-3-sonnet", "provider": "openrouter"}
            ]
        },
        "max_retries": 3
    }


def create_llm_config(model_name: str = "gpt-4o-mini", provider: str = "openrouter") -> Dict[str, Any]:
    """Создание конфигурации для LLM модели"""
    
    # Проверяем наличие API ключей
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if provider == "openrouter" and openrouter_key:
        return {
            "config_list": [{
                "model": model_name,
                "api_key": openrouter_key,
                "base_url": "https://openrouter.ai/api/v1",
                "temperature": 0.7,
                "max_tokens": 2000
            }],
            "timeout": 60,
            "cache_seed": None,  # Отключаем кеширование для более свежих ответов
        }
    
    elif provider == "openai" and openai_key:
        return {
            "config_list": [{
                "model": model_name,
                "api_key": openai_key,
                "temperature": 0.7,
                "max_tokens": 2000
            }],
            "timeout": 60,
            "cache_seed": None,
        }
    
    else:
        # Fallback конфигурация для режима без API
        print(f"⚠️ API ключ для {provider} не найден, используем mock конфигурацию")
        return {
            "config_list": [{
                "model": "mock_model",
                "api_key": "mock_key",
                "base_url": "http://localhost:8000"  # Несуществующий endpoint
            }],
            "timeout": 5,
        }


def get_model_by_tier(tier: str = "cheap", attempt: int = 0) -> Dict[str, Any]:
    """Получение модели по уровню и попытке"""
    tiers_config = load_llm_tiers()
    
    tier_models = tiers_config.get("tiers", {}).get(tier, [])
    
    if not tier_models:
        # Fallback к дешевой модели
        tier_models = tiers_config.get("tiers", {}).get("cheap", [])
    
    if attempt >= len(tier_models):
        # Если исчерпали модели в tier, берем последнюю
        model_info = tier_models[-1] if tier_models else {"name": "gpt-3.5-turbo", "provider": "openrouter"}
    else:
        model_info = tier_models[attempt]
    
    return create_llm_config(model_info["name"], model_info["provider"])


def upgrade_tier(current_tier: str) -> str:
    """Повышение уровня модели при ошибках"""
    tier_order = ["cheap", "standard", "premium"]
    
    try:
        current_index = tier_order.index(current_tier)
        if current_index < len(tier_order) - 1:
            return tier_order[current_index + 1]
    except ValueError:
        pass
    
    return "premium"  # Максимальный уровень


def validate_api_keys() -> Dict[str, bool]:
    """Проверка наличия API ключей"""
    return {
        "openrouter": bool(os.getenv('OPENROUTER_API_KEY')),
        "openai": bool(os.getenv('OPENAI_API_KEY')),
        "yandex": bool(os.getenv('YANDEX_GPT_API_KEY')),
        "anthropic": bool(os.getenv('ANTHROPIC_API_KEY')),
    }


def get_available_models() -> List[str]:
    """Получение списка доступных моделей на основе API ключей"""
    api_status = validate_api_keys()
    tiers_config = load_llm_tiers()
    
    available_models = []
    
    for tier_name, models in tiers_config.get("tiers", {}).items():
        for model in models:
            provider = model.get("provider", "openrouter")
            if api_status.get(provider, False):
                available_models.append(f"{model['name']} ({tier_name})")
    
    return available_models


if __name__ == "__main__":
    # Тестирование модуля
    print("🧪 Тестирование LLM конфигурации")
    print("=" * 50)
    
    # Проверяем API ключи
    api_status = validate_api_keys()
    print("🔑 Статус API ключей:")
    for provider, available in api_status.items():
        status = "✅" if available else "❌"
        print(f"  {status} {provider}")
    
    # Показываем доступные модели
    models = get_available_models()
    print(f"\n🤖 Доступные модели ({len(models)}):")
    for model in models:
        print(f"  • {model}")
    
    # Тестируем конфигурацию
    print(f"\n⚙️ Тестовая конфигурация:")
    config = get_model_by_tier("cheap", 0)
    print(f"  Model: {config['config_list'][0]['model']}")
    print(f"  Provider: {config['config_list'][0].get('base_url', 'OpenAI')}")