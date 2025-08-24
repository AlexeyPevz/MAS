"""
Function Calling Example
Демонстрация агентского поведения с инструментами
"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel
import json
import requests
from datetime import datetime
import sqlite3
from abc import ABC, abstractmethod

# Базовый класс для инструментов
class Tool(BaseModel, ABC):
    name: str
    description: str
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Возвращает JSON схему для LLM"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters_schema()
        }
    
    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        pass

# Инструмент для поиска в интернете
class WebSearchTool(Tool):
    name: str = "web_search"
    description: str = "Поиск информации в интернете"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Поисковый запрос"
                },
                "max_results": {
                    "type": "integer", 
                    "description": "Максимальное количество результатов",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    
    def execute(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Симуляция веб-поиска"""
        # В реальности здесь был бы вызов поискового API
        mock_results = [
            {
                "title": f"Результат {i+1} для '{query}'",
                "url": f"https://example.com/result-{i+1}",
                "snippet": f"Это краткое описание результата {i+1} по запросу '{query}'"
            }
            for i in range(min(max_results, 3))
        ]
        
        return {
            "success": True,
            "query": query,
            "results": mock_results,
            "total_found": len(mock_results)
        }

# Инструмент для работы с базой данных
class DatabaseTool(Tool):
    name: str = "database_query"
    description: str = "Выполнение SQL запросов к базе данных"
    
    def __init__(self, db_path: str = ":memory:"):
        super().__init__()
        self.db_path = db_path
        self._init_demo_db()
    
    def _init_demo_db(self):
        """Создает демо базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу проектов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                tech_stack TEXT,
                team_size INTEGER,
                budget REAL
            )
        """)
        
        # Добавляем демо данные
        demo_projects = [
            (1, "Проект X", "active", "React, Node.js, PostgreSQL", 8, 500000),
            (2, "Проект Y", "completed", "Vue.js, Python, MongoDB", 5, 300000),
            (3, "Проект Z", "planning", "Svelte, Go, Redis", 12, 800000)
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO projects VALUES (?, ?, ?, ?, ?, ?)",
            demo_projects
        )
        
        conn.commit()
        conn.close()
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SQL запрос для выполнения"
                }
            },
            "required": ["query"]
        }
    
    def execute(self, query: str) -> Dict[str, Any]:
        """Выполняет SQL запрос"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(query)
            
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                # Преобразуем в список словарей
                data = [dict(zip(columns, row)) for row in results]
                
                return {
                    "success": True,
                    "data": data,
                    "row_count": len(data)
                }
            else:
                conn.commit()
                return {
                    "success": True,
                    "message": "Запрос выполнен успешно",
                    "rows_affected": cursor.rowcount
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            conn.close()

# Инструмент для отправки email (симуляция)
class EmailTool(Tool):
    name: str = "send_email"
    description: str = "Отправка email сообщений"
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Email получателя"
                },
                "subject": {
                    "type": "string", 
                    "description": "Тема письма"
                },
                "body": {
                    "type": "string",
                    "description": "Текст письма"
                }
            },
            "required": ["to", "subject", "body"]
        }
    
    def execute(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Симуляция отправки email"""
        # В реальности здесь был бы вызов email API
        return {
            "success": True,
            "message": f"Email отправлен на {to}",
            "subject": subject,
            "timestamp": datetime.now().isoformat()
        }

# Менеджер инструментов
class ToolManager:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool):
        """Регистрирует инструмент"""
        self.tools[tool.name] = tool
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Возвращает схемы всех инструментов для LLM"""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Выполняет инструмент"""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        try:
            return self.tools[tool_name].execute(**kwargs)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}

# Агент с Function Calling
class FunctionCallingAgent:
    def __init__(self, tool_manager: ToolManager):
        self.tool_manager = tool_manager
        self.conversation_history = []
    
    def create_function_calling_prompt(self, user_query: str) -> str:
        """Создает промпт для Function Calling"""
        tools_schema = self.tool_manager.get_tools_schema()
        
        prompt = f"""
Ты помощник с доступом к инструментам. Проанализируй запрос пользователя и определи, какие инструменты нужно использовать.

ЗАПРОС ПОЛЬЗОВАТЕЛЯ: {user_query}

ДОСТУПНЫЕ ИНСТРУМЕНТЫ:
{json.dumps(tools_schema, ensure_ascii=False, indent=2)}

Если нужно использовать инструменты, верни JSON в формате:
{{
    "reasoning": "Объяснение, почему выбраны эти инструменты",
    "tool_calls": [
        {{
            "tool_name": "название_инструмента",
            "parameters": {{
                "param1": "value1",
                "param2": "value2"
            }}
        }}
    ]
}}

Если инструменты не нужны, верни:
{{
    "reasoning": "Объяснение, почему инструменты не нужны", 
    "response": "Прямой ответ на запрос"
}}
"""
        return prompt
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Обрабатывает запрос пользователя"""
        # В реальности здесь был бы вызов LLM
        # Симулируем ответ LLM
        
        if "проект" in user_query.lower():
            # LLM решает использовать database_query
            llm_response = {
                "reasoning": "Пользователь спрашивает о проектах, нужно обратиться к базе данных",
                "tool_calls": [
                    {
                        "tool_name": "database_query",
                        "parameters": {
                            "query": "SELECT * FROM projects"
                        }
                    }
                ]
            }
        elif "поиск" in user_query.lower() or "найди" in user_query.lower():
            # LLM решает использовать web_search
            llm_response = {
                "reasoning": "Нужно найти информацию в интернете",
                "tool_calls": [
                    {
                        "tool_name": "web_search", 
                        "parameters": {
                            "query": user_query,
                            "max_results": 3
                        }
                    }
                ]
            }
        else:
            # Прямой ответ без инструментов
            llm_response = {
                "reasoning": "Могу ответить без использования инструментов",
                "response": f"Понял ваш запрос: '{user_query}'. Это базовый ответ без использования инструментов."
            }
        
        # Выполняем инструменты если они указаны
        if "tool_calls" in llm_response:
            tool_results = []
            for tool_call in llm_response["tool_calls"]:
                result = self.tool_manager.execute_tool(
                    tool_call["tool_name"],
                    **tool_call["parameters"]
                )
                tool_results.append({
                    "tool_name": tool_call["tool_name"],
                    "result": result
                })
            
            # В реальности здесь был бы второй вызов LLM для обработки результатов
            final_response = self._process_tool_results(user_query, tool_results)
        else:
            final_response = llm_response["response"]
        
        return {
            "user_query": user_query,
            "llm_reasoning": llm_response.get("reasoning"),
            "tool_calls": llm_response.get("tool_calls", []),
            "tool_results": tool_results if "tool_calls" in llm_response else [],
            "final_response": final_response
        }
    
    def _process_tool_results(self, user_query: str, tool_results: List[Dict]) -> str:
        """Обрабатывает результаты инструментов (симуляция второго вызова LLM)"""
        if not tool_results:
            return "Не удалось получить результаты от инструментов."
        
        # Симулируем обработку результатов
        response_parts = [f"На основе вашего запроса '{user_query}' я получил следующую информацию:"]
        
        for tool_result in tool_results:
            tool_name = tool_result["tool_name"]
            result = tool_result["result"]
            
            if tool_name == "database_query" and result.get("success"):
                data = result.get("data", [])
                response_parts.append(f"Найдено {len(data)} проектов в базе данных:")
                for project in data:
                    response_parts.append(f"- {project.get('name')}: {project.get('status')} ({project.get('tech_stack')})")
            
            elif tool_name == "web_search" and result.get("success"):
                results = result.get("results", [])
                response_parts.append(f"Найдено {len(results)} результатов в интернете:")
                for item in results:
                    response_parts.append(f"- {item.get('title')}: {item.get('snippet')}")
        
        return "\n".join(response_parts)

# Демонстрация
if __name__ == "__main__":
    # Настройка инструментов
    tool_manager = ToolManager()
    tool_manager.register_tool(WebSearchTool())
    tool_manager.register_tool(DatabaseTool())
    tool_manager.register_tool(EmailTool())
    
    # Создание агента
    agent = FunctionCallingAgent(tool_manager)
    
    # Примеры запросов
    test_queries = [
        "Покажи все проекты в базе данных",
        "Найди информацию о современных фреймворках JavaScript",
        "Как дела?"
    ]
    
    print("=== FUNCTION CALLING ДЕМОНСТРАЦИЯ ===\n")
    
    for query in test_queries:
        print(f"ЗАПРОС: {query}")
        print("-" * 50)
        
        result = agent.process_query(query)
        
        print(f"LLM РАССУЖДЕНИЕ: {result['llm_reasoning']}")
        if result['tool_calls']:
            print(f"ВЫЗВАННЫЕ ИНСТРУМЕНТЫ: {[call['tool_name'] for call in result['tool_calls']]}")
        print(f"ОТВЕТ: {result['final_response']}")
        print("\n" + "="*70 + "\n")
    
    print("=== СХЕМЫ ИНСТРУМЕНТОВ ===")
    print(json.dumps(tool_manager.get_tools_schema(), ensure_ascii=False, indent=2))