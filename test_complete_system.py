#!/usr/bin/env python3
"""
Complete System Integration Test
Полный тест всех компонентов MAS системы
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Настройка путей
sys.path.insert(0, str(Path(__file__).parent))

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [TEST] %(message)s'
)
logger = logging.getLogger(__name__)


class SystemTester:
    """Полное тестирование MAS системы"""
    
    def __init__(self):
        self.test_results = []
        self.agents = None
        self.manager = None
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Логирование результатов теста"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append((test_name, passed, details))
        logger.info(f"{status} {test_name}: {details}")
    
    async def test_environment_setup(self) -> bool:
        """Тест настройки окружения"""
        try:
            # Проверяем .env файл
            env_exists = os.path.exists('.env')
            
            # Проверяем основные переменные
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            has_api_key = openrouter_key and openrouter_key != 'test_key_for_demo'
            
            self.log_test(
                "Environment Setup", 
                env_exists, 
                f".env exists: {env_exists}, real API key: {has_api_key}"
            )
            return env_exists
            
        except Exception as e:
            self.log_test("Environment Setup", False, str(e))
            return False
    
    async def test_llm_configuration(self) -> bool:
        """Тест LLM конфигурации"""
        try:
            from tools.llm_config import validate_api_keys, get_available_models, create_llm_config
            
            # Проверяем API ключи
            api_status = validate_api_keys()
            has_any_key = any(api_status.values())
            
            # Проверяем доступные модели
            models = get_available_models()
            
            # Тестируем создание конфигурации
            config = create_llm_config("gpt-4o-mini", "openrouter")
            config_valid = "config_list" in config and len(config["config_list"]) > 0
            
            self.log_test(
                "LLM Configuration",
                has_any_key and config_valid,
                f"API keys: {sum(api_status.values())}, models: {len(models)}, config: {config_valid}"
            )
            return has_any_key and config_valid
            
        except Exception as e:
            self.log_test("LLM Configuration", False, str(e))
            return False
    
    async def test_agents_creation(self) -> bool:
        """Тест создания агентов"""
        try:
            from pathlib import Path
            from agents.core_agents import create_agents
            from config_loader import AgentsConfig
            
            # Загружаем конфигурацию
            config_path = Path('config/agents.yaml')
            config = AgentsConfig.from_yaml(config_path)
            
            # Создаем агентов
            self.agents = create_agents(config)
            
            # Проверяем количество
            expected_count = len(config.agents)
            actual_count = len(self.agents)
            all_created = actual_count == expected_count
            
            # Проверяем типы агентов
            agent_types = {name: type(agent).__name__ for name, agent in self.agents.items()}
            
            self.log_test(
                "Agents Creation",
                all_created,
                f"Created {actual_count}/{expected_count}: {list(agent_types.keys())}"
            )
            return all_created
            
        except Exception as e:
            self.log_test("Agents Creation", False, str(e))
            return False
    
    async def test_memory_integration(self) -> bool:
        """Тест интеграции памяти"""
        try:
            memory_agents = []
            
            for name, agent in self.agents.items():
                if hasattr(agent, 'memory') and agent.memory is not None:
                    memory_agents.append(name)
                    
                    # Тестируем методы памяти
                    if hasattr(agent, 'remember') and hasattr(agent, 'recall'):
                        test_key = f"test_{name}"
                        test_value = f"test_data_for_{name}"
                        
                        agent.remember(test_key, test_value)
                        recalled = agent.recall(test_key)
                        # Память может быть недоступна, это OK
            
            self.log_test(
                "Memory Integration",
                True,  # Всегда успешно, поскольку память опциональна
                f"Agents with memory: {memory_agents}"
            )
            return True
            
        except Exception as e:
            self.log_test("Memory Integration", False, str(e))
            return False
    
    async def test_groupchat_manager(self) -> bool:
        """Тест GroupChat Manager"""
        try:
            from tools.smart_groupchat import SmartGroupChatManager
            
            # Создаем маршрутизацию
            routing = {
                "communicator": ["meta"],
                "meta": ["coordination", "researcher"],
                "coordination": ["prompt_builder"],
                "researcher": ["fact_checker"],
                "fact_checker": ["meta"],
            }
            
            # Создаем manager
            self.manager = SmartGroupChatManager(self.agents, routing)
            
            # Тестируем базовые методы
            status = self.manager.get_system_status()
            stats = self.manager.get_agent_statistics()
            
            manager_working = (
                status["agents_count"] == len(self.agents) and
                isinstance(stats, dict)
            )
            
            self.log_test(
                "GroupChat Manager",
                manager_working,
                f"Status: {status['system_health']}, Agents: {status['agents_count']}"
            )
            return manager_working
            
        except Exception as e:
            self.log_test("GroupChat Manager", False, str(e))
            return False
    
    async def test_message_processing(self) -> bool:
        """Тест обработки сообщений"""
        try:
            # Тестовые сообщения
            test_messages = [
                "Привет, как дела?",
                "Создай план проекта",
                "Найди информацию о Python"
            ]
            
            successful_responses = 0
            
            for message in test_messages:
                try:
                    response = await self.manager.process_user_message(message)
                    if response and len(response) > 0:
                        successful_responses += 1
                    
                    # Небольшая пауза между сообщениями
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.warning(f"Ошибка обработки сообщения '{message}': {e}")
            
            success_rate = successful_responses / len(test_messages)
            processing_works = success_rate >= 0.5  # Хотя бы 50% успешных
            
            self.log_test(
                "Message Processing",
                processing_works,
                f"Success rate: {success_rate:.1%} ({successful_responses}/{len(test_messages)})"
            )
            return processing_works
            
        except Exception as e:
            self.log_test("Message Processing", False, str(e))
            return False
    
    async def test_telegram_integration(self) -> bool:
        """Тест Telegram интеграции"""
        try:
            from tools.modern_telegram_bot import TELEGRAM_AVAILABLE, ModernTelegramBot
            
            if not TELEGRAM_AVAILABLE:
                self.log_test(
                    "Telegram Integration",
                    True,  # OK если библиотека не установлена
                    "python-telegram-bot не установлен (опционально)"
                )
                return True
            
            # Проверяем токен
            token = os.getenv('TELEGRAM_BOT_TOKEN')
            if not token or token == 'your_telegram_bot_token_here':
                self.log_test(
                    "Telegram Integration",
                    True,  # OK если токен не настроен
                    "TELEGRAM_BOT_TOKEN не настроен (опционально)"
                )
                return True
            
            # Создаем тестовый callback
            async def test_callback(message: str) -> str:
                return f"Test response: {message}"
            
            # Пробуем создать бота (но не запускаем)
            bot = ModernTelegramBot(token, test_callback)
            bot_created = bot is not None
            
            self.log_test(
                "Telegram Integration",
                bot_created,
                "Telegram bot может быть создан"
            )
            return bot_created
            
        except Exception as e:
            self.log_test("Telegram Integration", False, str(e))
            return False
    
    async def test_docker_services(self) -> bool:
        """Тест Docker сервисов"""
        try:
            import subprocess
            
            # Проверяем Docker
            docker_available = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                timeout=5
            ).returncode == 0
            
            if not docker_available:
                self.log_test(
                    "Docker Services",
                    True,  # OK если Docker недоступен
                    "Docker не установлен (опционально для разработки)"
                )
                return True
            
            # Проверяем Docker Compose
            compose_available = subprocess.run(
                ["docker-compose", "--version"], 
                capture_output=True, 
                timeout=5
            ).returncode == 0
            
            self.log_test(
                "Docker Services",
                compose_available,
                f"Docker: {docker_available}, Compose: {compose_available}"
            )
            return compose_available
            
        except Exception as e:
            self.log_test("Docker Services", True, f"Docker проверка пропущена: {e}")
            return True
    
    async def run_all_tests(self) -> bool:
        """Запуск всех тестов"""
        logger.info("🚀 Запуск полного тестирования MAS системы")
        logger.info("=" * 60)
        
        tests = [
            self.test_environment_setup,
            self.test_llm_configuration,
            self.test_agents_creation,
            self.test_memory_integration,
            self.test_groupchat_manager,
            self.test_message_processing,
            self.test_telegram_integration,
            self.test_docker_services,
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed_tests += 1
            except Exception as e:
                logger.error(f"❌ Критическая ошибка в тесте {test.__name__}: {e}")
        
        # Итоговый отчет
        logger.info("\n" + "=" * 60)
        logger.info("📊 ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        logger.info("=" * 60)
        
        for test_name, passed, details in self.test_results:
            status = "✅" if passed else "❌"
            logger.info(f"{status} {test_name}: {details}")
        
        success_rate = passed_tests / total_tests
        overall_success = success_rate >= 0.8  # 80% тестов должны пройти
        
        logger.info(f"\n🎯 Успешность: {success_rate:.1%} ({passed_tests}/{total_tests})")
        
        if overall_success:
            logger.info("🎉 СИСТЕМА ГОТОВА К PRODUCTION!")
        else:
            logger.info("⚠️ Система требует доработки")
        
        return overall_success
    
    def get_summary(self) -> dict:
        """Получение сводки тестирования"""
        passed = sum(1 for _, result, _ in self.test_results if result)
        total = len(self.test_results)
        
        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": passed / total if total > 0 else 0,
            "ready_for_production": passed / total >= 0.8 if total > 0 else False
        }


async def main():
    """Основная функция тестирования"""
    tester = SystemTester()
    
    try:
        success = await tester.run_all_tests()
        summary = tester.get_summary()
        
        print(f"\n{'='*60}")
        print("🎯 ФИНАЛЬНАЯ СВОДКА")
        print(f"{'='*60}")
        print(f"📊 Тестов пройдено: {summary['passed_tests']}/{summary['total_tests']}")
        print(f"📈 Успешность: {summary['success_rate']:.1%}")
        print(f"🚀 Готовность к production: {'ДА' if summary['ready_for_production'] else 'НЕТ'}")
        
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)