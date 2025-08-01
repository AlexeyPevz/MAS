"""
gemini_cli.py
=============

Интеграция Google Gemini CLI для MAC системы.
Предоставляет возможность использования Gemini 2.5 Pro через командную строку.
"""

import os
import json
import asyncio
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class GeminiCLI:
    """Обертка для работы с Gemini CLI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация Gemini CLI.
        
        Args:
            api_key: API ключ для Gemini (опционально, можно использовать логин через Google)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._setup_environment()
        
    def _setup_environment(self):
        """Настройка окружения для Gemini CLI."""
        if self.api_key:
            os.environ["GEMINI_API_KEY"] = self.api_key
            
    async def execute(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполнить запрос к Gemini CLI.
        
        Args:
            prompt: Текст запроса
            context: Дополнительный контекст (файлы, настройки и т.д.)
            
        Returns:
            Словарь с результатом выполнения
        """
        try:
            # Формируем команду
            cmd = ["gemini", prompt]
            
            # Добавляем контекстные файлы если есть
            if context and "files" in context:
                for file_path in context["files"]:
                    if Path(file_path).exists():
                        cmd.extend(["--file", file_path])
            
            # Выполняем команду асинхронно
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                text=False
            )
            
            stdout, stderr = await process.communicate()
            
            # Декодируем вывод
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            if process.returncode != 0:
                logger.error(f"Gemini CLI error: {stderr_text}")
                return {
                    "success": False,
                    "error": stderr_text,
                    "response": None
                }
                
            return {
                "success": True,
                "response": stdout_text,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Exception in Gemini CLI: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    async def code_assistant(self, task: str, files: List[str] = None) -> Dict[str, Any]:
        """
        Использовать Gemini для помощи с кодом.
        
        Args:
            task: Описание задачи
            files: Список файлов для контекста
            
        Returns:
            Результат выполнения
        """
        prompt = f"As a code assistant, {task}"
        context = {"files": files} if files else None
        return await self.execute(prompt, context)
    
    async def analyze_code(self, file_path: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Анализ кода с помощью Gemini.
        
        Args:
            file_path: Путь к файлу для анализа
            analysis_type: Тип анализа (general, security, performance, etc.)
            
        Returns:
            Результат анализа
        """
        analysis_prompts = {
            "general": "Analyze this code and provide insights",
            "security": "Perform a security audit on this code",
            "performance": "Analyze performance bottlenecks in this code",
            "refactor": "Suggest refactoring improvements for this code"
        }
        
        prompt = analysis_prompts.get(analysis_type, analysis_prompts["general"])
        return await self.execute(prompt, {"files": [file_path]})
    
    async def generate_tests(self, file_path: str) -> Dict[str, Any]:
        """
        Генерация тестов для кода.
        
        Args:
            file_path: Путь к файлу с кодом
            
        Returns:
            Сгенерированные тесты
        """
        prompt = "Generate comprehensive unit tests for this code"
        return await self.execute(prompt, {"files": [file_path]})
    
    async def debug_error(self, error_message: str, context_files: List[str] = None) -> Dict[str, Any]:
        """
        Помощь в отладке ошибок.
        
        Args:
            error_message: Сообщение об ошибке
            context_files: Файлы с контекстом
            
        Returns:
            Предложения по исправлению
        """
        prompt = f"Help debug this error: {error_message}"
        context = {"files": context_files} if context_files else None
        return await self.execute(prompt, context)
    
    async def research(self, topic: str) -> Dict[str, Any]:
        """
        Исследование темы с использованием Google Search.
        
        Args:
            topic: Тема для исследования
            
        Returns:
            Результаты исследования
        """
        prompt = f"Research and provide comprehensive information about: {topic}"
        return await self.execute(prompt)
    
    async def generate_documentation(self, file_path: str) -> Dict[str, Any]:
        """
        Генерация документации для кода.
        
        Args:
            file_path: Путь к файлу с кодом
            
        Returns:
            Сгенерированная документация
        """
        prompt = "Generate comprehensive documentation for this code"
        return await self.execute(prompt, {"files": [file_path]})


# Singleton для глобального использования
_gemini_instance = None

def get_gemini_cli() -> GeminiCLI:
    """Получить экземпляр Gemini CLI."""
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiCLI()
    return _gemini_instance


# Пример использования для тестирования
async def test_gemini_cli():
    """Тест функциональности Gemini CLI."""
    gemini = get_gemini_cli()
    
    # Тест простого запроса
    result = await gemini.execute("What is Python?")
    print(f"Simple query result: {result}")
    
    # Тест анализа кода
    if Path("run_system.py").exists():
        analysis = await gemini.analyze_code("run_system.py", "general")
        print(f"Code analysis: {analysis}")


if __name__ == "__main__":
    asyncio.run(test_gemini_cli())