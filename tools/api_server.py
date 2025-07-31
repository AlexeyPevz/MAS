"""
MAS RESTful API Server
Сервер для внешних интеграций с MAS системой
"""
import asyncio
import logging
from aiohttp import web
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

# Импорты для интеграции с MAS
from tools.smart_groupchat import SmartGroupChatManager
from tools.llm_config import validate_api_keys, get_available_models
from tools.budget_manager import BudgetManager
from config.config_loader import AgentsConfig
from agents.core_agents import create_agents
from pathlib import Path

logger = logging.getLogger(__name__)


class MASAPIServer:
    """RESTful API сервер для MAS системы"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.manager: Optional[SmartGroupChatManager] = None
        self.agents = {}
        self.budget_manager = BudgetManager(daily_limit=100.0)
        
        # Настройка маршрутов
        self._setup_routes()
        
        # Статистика API
        self.stats = {
            "requests": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
    
    def _setup_routes(self):
        """Настройка API endpoints"""
        self.app.router.add_routes([
            # Основные endpoints
            web.get('/api/v1/health', self.health_check),
            web.get('/api/v1/status', self.get_status),
            web.get('/api/v1/models', self.get_models),
            
            # Работа с сообщениями
            web.post('/api/v1/messages', self.process_message),
            web.get('/api/v1/messages/history', self.get_history),
            
            # Управление агентами
            web.get('/api/v1/agents', self.list_agents),
            web.get('/api/v1/agents/{agent_name}', self.get_agent_info),
            
            # Управление задачами
            web.post('/api/v1/tasks', self.create_task),
            web.get('/api/v1/tasks', self.list_tasks),
            web.get('/api/v1/tasks/{task_id}', self.get_task),
            
            # Бюджет и статистика
            web.get('/api/v1/budget', self.get_budget),
            web.get('/api/v1/statistics', self.get_statistics),
            
            # Вебхуки
            web.post('/api/v1/webhooks/telegram', self.telegram_webhook),
        ])
        
        # CORS middleware
        self.app.middlewares.append(self._cors_middleware)
        
        # Error handling middleware
        self.app.middlewares.append(self._error_middleware)
    
    @web.middleware
    async def _cors_middleware(self, request, handler):
        """CORS middleware для кросс-доменных запросов"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @web.middleware
    async def _error_middleware(self, request, handler):
        """Обработка ошибок"""
        try:
            self.stats["requests"] += 1
            return await handler(request)
        except web.HTTPException:
            raise
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"API Error: {e}")
            return web.json_response({
                "error": str(e),
                "type": type(e).__name__
            }, status=500)
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })
    
    async def get_status(self, request):
        """Получение статуса системы"""
        if not self.manager:
            return web.json_response({
                "error": "System not initialized"
            }, status=503)
        
        status = self.manager.get_system_status()
        api_stats = self.get_api_stats()
        
        return web.json_response({
            "system": status,
            "api": api_stats,
            "timestamp": datetime.now().isoformat()
        })
    
    async def get_models(self, request):
        """Получение списка доступных моделей"""
        models = get_available_models()
        api_status = validate_api_keys()
        
        return web.json_response({
            "models": models,
            "providers": api_status,
            "total": len(models)
        })
    
    async def process_message(self, request):
        """Обработка сообщения через MAS"""
        if not self.manager:
            return web.json_response({
                "error": "System not initialized"
            }, status=503)
        
        try:
            data = await request.json()
            message = data.get("message")
            user_id = data.get("user_id", "api_user")
            
            if not message:
                return web.json_response({
                    "error": "Message is required"
                }, status=400)
            
            # Обработка через MAS
            response = await self.manager.process_user_message(message, user_id)
            
            return web.json_response({
                "response": response,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def get_history(self, request):
        """Получение истории разговора"""
        if not self.manager:
            return web.json_response({
                "error": "System not initialized"
            }, status=503)
        
        limit = int(request.query.get('limit', 50))
        
        # Получаем последние сообщения
        history = []
        for msg in self.manager.conversation_history[-limit:]:
            history.append({
                "sender": msg.sender,
                "recipient": msg.recipient,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "type": msg.message_type,
                "metadata": msg.metadata
            })
        
        return web.json_response({
            "history": history,
            "total": len(self.manager.conversation_history),
            "limit": limit
        })
    
    async def list_agents(self, request):
        """Список всех агентов"""
        agents_info = {}
        for name, agent in self.agents.items():
            agents_info[name] = {
                "type": type(agent).__name__,
                "has_llm": hasattr(agent, 'llm_config'),
                "has_memory": hasattr(agent, 'memory')
            }
        
        return web.json_response({
            "agents": agents_info,
            "total": len(self.agents)
        })
    
    async def get_agent_info(self, request):
        """Информация о конкретном агенте"""
        agent_name = request.match_info['agent_name']
        
        if agent_name not in self.agents:
            return web.json_response({
                "error": "Agent not found"
            }, status=404)
        
        agent = self.agents[agent_name]
        
        info = {
            "name": agent_name,
            "type": type(agent).__name__,
            "has_llm": hasattr(agent, 'llm_config'),
            "has_memory": hasattr(agent, 'memory'),
            "system_message": getattr(agent, 'system_message', None)
        }
        
        # Статистика активности
        if self.manager:
            stats = self.manager.get_agent_statistics()
            info["messages_count"] = stats.get(agent_name, 0)
        
        return web.json_response(info)
    
    async def create_task(self, request):
        """Создание новой задачи"""
        if not self.manager:
            return web.json_response({
                "error": "System not initialized"
            }, status=503)
        
        try:
            data = await request.json()
            description = data.get("description")
            agent = data.get("agent", "meta")
            
            if not description:
                return web.json_response({
                    "error": "Task description is required"
                }, status=400)
            
            task_id = await self.manager.create_task(description, agent)
            
            return web.json_response({
                "task_id": task_id,
                "status": "created",
                "agent": agent
            })
            
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def list_tasks(self, request):
        """Список активных задач"""
        if not self.manager:
            return web.json_response({
                "error": "System not initialized"
            }, status=503)
        
        tasks = []
        for task_id, task_data in self.manager.active_tasks.items():
            tasks.append({
                "id": task_id,
                "description": task_data["description"],
                "agent": task_data["assigned_agent"],
                "status": task_data["status"],
                "created_at": task_data["created_at"].isoformat(),
                "result": task_data.get("result")
            })
        
        return web.json_response({
            "tasks": tasks,
            "total": len(tasks)
        })
    
    async def get_task(self, request):
        """Получение информации о задаче"""
        if not self.manager:
            return web.json_response({
                "error": "System not initialized"
            }, status=503)
        
        task_id = request.match_info['task_id']
        
        if task_id not in self.manager.active_tasks:
            return web.json_response({
                "error": "Task not found"
            }, status=404)
        
        task = self.manager.active_tasks[task_id]
        
        return web.json_response({
            "id": task_id,
            "description": task["description"],
            "agent": task["assigned_agent"],
            "status": task["status"],
            "created_at": task["created_at"].isoformat(),
            "result": task.get("result")
        })
    
    async def get_budget(self, request):
        """Получение информации о бюджете"""
        budget_info = {
            "daily_limit": self.budget_manager.daily_limit,
            "spent_today": self.budget_manager.get_daily_spent(),
            "remaining": self.budget_manager.get_remaining_budget(),
            "is_over_budget": self.budget_manager.is_over_budget()
        }
        
        return web.json_response(budget_info)
    
    async def get_statistics(self, request):
        """Получение статистики системы"""
        stats = {
            "api": self.get_api_stats()
        }
        
        if self.manager:
            stats["agents"] = self.manager.get_agent_statistics()
            stats["conversation"] = self.manager.get_conversation_summary()
        
        return web.json_response(stats)
    
    async def telegram_webhook(self, request):
        """Webhook для Telegram бота"""
        try:
            data = await request.json()
            # Здесь обработка webhook от Telegram
            logger.info(f"Telegram webhook: {data}")
            
            return web.json_response({"status": "ok"})
            
        except Exception as e:
            logger.error(f"Telegram webhook error: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    def get_api_stats(self) -> Dict[str, Any]:
        """Получение статистики API"""
        uptime = datetime.now() - self.stats["start_time"]
        
        return {
            "requests": self.stats["requests"],
            "errors": self.stats["errors"],
            "uptime": str(uptime),
            "error_rate": self.stats["errors"] / max(self.stats["requests"], 1)
        }
    
    async def initialize_mas(self):
        """Инициализация MAS системы"""
        logger.info("🚀 Инициализация MAS для API сервера...")
        
        try:
            # Загружаем конфигурацию
            config_path = Path('config/agents.yaml')
            config = AgentsConfig.from_yaml(config_path)
            
            # Создаем агентов
            self.agents = create_agents(config)
            
            # Настройка маршрутизации
            routing = {
                "communicator": ["meta"],
                "meta": ["coordination", "researcher"],
                "coordination": ["prompt_builder", "workflow_builder", "webapp_builder"],
                "researcher": ["fact_checker"],
                "fact_checker": ["meta"],
                "prompt_builder": ["model_selector"],
                "model_selector": ["agent_builder"],
                "agent_builder": ["instance_factory"],
                "multi_tool": ["workflow_builder", "webapp_builder"],
                "workflow_builder": ["multi_tool"],
                "webapp_builder": ["multi_tool"],
                "instance_factory": ["coordination"]
            }
            
            # Создаем менеджер
            self.manager = SmartGroupChatManager(self.agents, routing)
            
            logger.info("✅ MAS система инициализирована для API")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации MAS: {e}")
            raise
    
    async def start(self):
        """Запуск API сервера"""
        # Инициализация MAS
        await self.initialize_mas()
        
        # Создание runner
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        # Запуск сайта
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info(f"🌐 API сервер запущен на http://{self.host}:{self.port}")
        logger.info("📖 API документация: http://{self.host}:{self.port}/api/v1/")
        
        # Ожидание остановки
        await asyncio.Event().wait()


# Функция для запуска из production_launcher
async def start_api_server(host: str = "0.0.0.0", port: int = 8080) -> MASAPIServer:
    """Запуск API сервера"""
    server = MASAPIServer(host, port)
    asyncio.create_task(server.start())
    return server


if __name__ == "__main__":
    # Автономный запуск
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        server = MASAPIServer()
        await server.start()
    
    asyncio.run(main())