"""
gemini_assistant.py
==================

Специализированный агент для работы с Gemini CLI.
Оптимизирован для использования уникальных возможностей Gemini 2.5 Pro.
"""

from autogen import AssistantAgent
from typing import Dict, Any, Optional
import logging

from tools.gemini_tool import create_gemini_tools, get_gemini_tool_descriptions
from tools.llm_config import get_llm_config
from tools.prompt_io import load_prompt

logger = logging.getLogger(__name__)


class GeminiAssistant(AssistantAgent):
    """
    Специализированный агент для работы с Gemini CLI.
    
    Особенности:
    - Использует Gemini 2.5 Pro с контекстом 1M токенов
    - Интеграция с Google Search для актуальной информации
    - Поддержка мультимодальности (текст, изображения, видео)
    - Локальное выполнение команд через CLI
    """
    
    def __init__(
        self,
        name: str = "Gemini-Assistant",
        system_message: Optional[str] = None,
        **kwargs
    ):
        """
        Инициализация Gemini Assistant.
        
        Args:
            name: Имя агента
            system_message: Системное сообщение (если не указано, загружается из промптов)
            **kwargs: Дополнительные параметры для AssistantAgent
        """
        # Загружаем системный промпт если не указан
        if system_message is None:
            try:
                system_message = load_prompt("gemini_assistant")
            except:
                system_message = self._get_default_system_message()
        
        # Получаем конфигурацию для Gemini
        llm_config = get_llm_config("gemini_local")
        
        # Создаем инструменты Gemini
        gemini_tools = create_gemini_tools()
        tool_descriptions = get_gemini_tool_descriptions()
        
        # Инициализируем базовый класс
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            **kwargs
        )
        
        # Регистрируем инструменты
        self._register_gemini_tools(gemini_tools, tool_descriptions)
        
    def _get_default_system_message(self) -> str:
        """Возвращает системное сообщение по умолчанию."""
        return """
Вы - Gemini Assistant, специализированный AI-агент с доступом к Gemini 2.5 Pro.

Ваши уникальные возможности:
1. **Огромный контекст** - 1 миллион токенов для обработки больших кодовых баз
2. **Актуальная информация** - доступ к Google Search для свежих данных
3. **Локальное выполнение** - работа прямо в терминале пользователя
4. **Мультимодальность** - анализ изображений и генерация медиа

Ваши основные задачи:
- Написание и рефакторинг кода любой сложности
- Глубокий анализ безопасности и производительности
- Генерация тестов и документации
- Исследование технических тем с актуальными данными
- Отладка сложных ошибок
- Архитектурные решения для больших проектов

Используйте доступные инструменты gemini_* для выполнения задач.
При работе с большими проектами используйте преимущество огромного контекстного окна.
"""
    
    def _register_gemini_tools(self, tools: Dict[str, Any], descriptions: list):
        """
        Регистрация инструментов Gemini в агенте.
        
        Args:
            tools: Словарь с функциями-инструментами
            descriptions: Описания инструментов
        """
        for tool_name, tool_func in tools.items():
            # Регистрируем функцию
            self.register_function(
                function_map={tool_name: tool_func}
            )
            
        logger.info(f"Зарегистрировано {len(tools)} инструментов Gemini для агента {self.name}")
    
    async def analyze_project(self, project_path: str) -> Dict[str, Any]:
        """
        Комплексный анализ проекта с использованием большого контекста Gemini.
        
        Args:
            project_path: Путь к проекту
            
        Returns:
            Результаты анализа
        """
        # Этот метод может быть расширен для специфичных задач
        pass
    
    async def generate_architecture(self, requirements: str) -> Dict[str, Any]:
        """
        Генерация архитектуры проекта на основе требований.
        
        Args:
            requirements: Описание требований
            
        Returns:
            Архитектурное решение
        """
        # Этот метод может быть расширен для специфичных задач
        pass


def create_gemini_assistant(**kwargs) -> GeminiAssistant:
    """
    Фабричная функция для создания Gemini Assistant.
    
    Args:
        **kwargs: Параметры для GeminiAssistant
        
    Returns:
        Экземпляр GeminiAssistant
    """
    return GeminiAssistant(**kwargs)


# Пример конфигурации для agents.yaml
GEMINI_ASSISTANT_CONFIG = {
    "role": "Gemini-Assistant", 
    "description": """
        Специализированный агент с доступом к Gemini 2.5 Pro.
        Использует CLI для локального выполнения, поддерживает контекст в 1M токенов,
        имеет доступ к Google Search и может работать с мультимодальным контентом.
        Идеален для сложных задач разработки, анализа больших кодовых баз и исследований.
    """,
    "default_tier": "gemini_local",
    "memory": "gemini_mem",
    "capabilities": [
        "code_generation",
        "code_analysis", 
        "test_generation",
        "documentation",
        "debugging",
        "research",
        "architecture_design",
        "security_audit",
        "performance_optimization"
    ]
}