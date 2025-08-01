"""
gemini_tool.py
==============

Инструменты для использования Gemini CLI в агентах AutoGen.
Предоставляет готовые функции для интеграции с существующими агентами.
"""

from typing import Dict, Any, List, Optional
import asyncio
from .gemini_cli import get_gemini_cli
import logging

logger = logging.getLogger(__name__)


def create_gemini_tools():
    """
    Создает набор инструментов Gemini для использования в агентах.
    
    Returns:
        Список функций-инструментов для AutoGen
    """
    
    gemini = get_gemini_cli()
    
    def gemini_code_assist(task: str, files: Optional[List[str]] = None) -> str:
        """
        Помощь с кодом через Gemini CLI.
        
        Args:
            task: Описание задачи (написать код, исправить ошибку, рефакторинг и т.д.)
            files: Список файлов для контекста
            
        Returns:
            Результат от Gemini
        """
        try:
            result = asyncio.run(gemini.code_assistant(task, files))
            if result["success"]:
                return result["response"]
            else:
                return f"Ошибка Gemini: {result['error']}"
        except Exception as e:
            logger.error(f"Ошибка в gemini_code_assist: {str(e)}")
            return f"Ошибка выполнения: {str(e)}"
    
    def gemini_analyze_code(file_path: str, analysis_type: str = "general") -> str:
        """
        Анализ кода с помощью Gemini.
        
        Args:
            file_path: Путь к файлу для анализа
            analysis_type: Тип анализа (general, security, performance, refactor)
            
        Returns:
            Результат анализа
        """
        try:
            result = asyncio.run(gemini.analyze_code(file_path, analysis_type))
            if result["success"]:
                return result["response"]
            else:
                return f"Ошибка Gemini: {result['error']}"
        except Exception as e:
            logger.error(f"Ошибка в gemini_analyze_code: {str(e)}")
            return f"Ошибка выполнения: {str(e)}"
    
    def gemini_generate_tests(file_path: str) -> str:
        """
        Генерация тестов для кода.
        
        Args:
            file_path: Путь к файлу с кодом
            
        Returns:
            Сгенерированные тесты
        """
        try:
            result = asyncio.run(gemini.generate_tests(file_path))
            if result["success"]:
                return result["response"]
            else:
                return f"Ошибка Gemini: {result['error']}"
        except Exception as e:
            logger.error(f"Ошибка в gemini_generate_tests: {str(e)}")
            return f"Ошибка выполнения: {str(e)}"
    
    def gemini_debug_error(error_message: str, context_files: Optional[List[str]] = None) -> str:
        """
        Помощь в отладке ошибок.
        
        Args:
            error_message: Сообщение об ошибке
            context_files: Файлы с контекстом
            
        Returns:
            Предложения по исправлению
        """
        try:
            result = asyncio.run(gemini.debug_error(error_message, context_files))
            if result["success"]:
                return result["response"]
            else:
                return f"Ошибка Gemini: {result['error']}"
        except Exception as e:
            logger.error(f"Ошибка в gemini_debug_error: {str(e)}")
            return f"Ошибка выполнения: {str(e)}"
    
    def gemini_research(topic: str) -> str:
        """
        Исследование темы с использованием Google Search.
        
        Args:
            topic: Тема для исследования
            
        Returns:
            Результаты исследования
        """
        try:
            result = asyncio.run(gemini.research(topic))
            if result["success"]:
                return result["response"]
            else:
                return f"Ошибка Gemini: {result['error']}"
        except Exception as e:
            logger.error(f"Ошибка в gemini_research: {str(e)}")
            return f"Ошибка выполнения: {str(e)}"
    
    def gemini_generate_docs(file_path: str) -> str:
        """
        Генерация документации для кода.
        
        Args:
            file_path: Путь к файлу с кодом
            
        Returns:
            Сгенерированная документация
        """
        try:
            result = asyncio.run(gemini.generate_documentation(file_path))
            if result["success"]:
                return result["response"]
            else:
                return f"Ошибка Gemini: {result['error']}"
        except Exception as e:
            logger.error(f"Ошибка в gemini_generate_docs: {str(e)}")
            return f"Ошибка выполнения: {str(e)}"
    
    def gemini_query(prompt: str) -> str:
        """
        Произвольный запрос к Gemini.
        
        Args:
            prompt: Текст запроса
            
        Returns:
            Ответ Gemini
        """
        try:
            result = asyncio.run(gemini.execute(prompt))
            if result["success"]:
                return result["response"]
            else:
                return f"Ошибка Gemini: {result['error']}"
        except Exception as e:
            logger.error(f"Ошибка в gemini_query: {str(e)}")
            return f"Ошибка выполнения: {str(e)}"
    
    # Возвращаем словарь с инструментами
    return {
        "gemini_code_assist": gemini_code_assist,
        "gemini_analyze_code": gemini_analyze_code,
        "gemini_generate_tests": gemini_generate_tests,
        "gemini_debug_error": gemini_debug_error,
        "gemini_research": gemini_research,
        "gemini_generate_docs": gemini_generate_docs,
        "gemini_query": gemini_query
    }


def get_gemini_tool_descriptions():
    """
    Получить описания инструментов для регистрации в агентах.
    
    Returns:
        Список описаний инструментов
    """
    return [
        {
            "name": "gemini_code_assist",
            "description": "Помощь с написанием, исправлением и улучшением кода через Gemini 2.5 Pro",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Описание задачи с кодом"
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Список файлов для контекста (опционально)"
                    }
                },
                "required": ["task"]
            }
        },
        {
            "name": "gemini_analyze_code",
            "description": "Анализ кода на предмет качества, безопасности, производительности",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Путь к файлу для анализа"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["general", "security", "performance", "refactor"],
                        "description": "Тип анализа"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "gemini_generate_tests",
            "description": "Автоматическая генерация тестов для кода",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Путь к файлу с кодом"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "gemini_debug_error",
            "description": "Помощь в отладке ошибок с использованием AI",
            "parameters": {
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "Сообщение об ошибке"
                    },
                    "context_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Файлы с контекстом (опционально)"
                    }
                },
                "required": ["error_message"]
            }
        },
        {
            "name": "gemini_research",
            "description": "Исследование темы с использованием Google Search и Gemini",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Тема для исследования"
                    }
                },
                "required": ["topic"]
            }
        },
        {
            "name": "gemini_generate_docs",
            "description": "Автоматическая генерация документации для кода",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Путь к файлу с кодом"
                    }
                },
                "required": ["file_path"]
            }
        },
        {
            "name": "gemini_query",
            "description": "Произвольный запрос к Gemini 2.5 Pro",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Текст запроса"
                    }
                },
                "required": ["prompt"]
            }
        }
    ]