"""
GroupChat Wrapper для совместимости с AutoGen
"""
from typing import Dict, List, Any
from pathlib import Path

# Пробуем импортировать разные версии autogen
try:
    from autogen.agentchat import ConversableAgent, GroupChat, GroupChatManager
except ImportError:
    try:
        # Новая версия autogen
        from autogen_agentchat import ConversableAgent, GroupChat, GroupChatManager
    except ImportError:
        # Fallback - создаем заглушки
        class ConversableAgent:
            def __init__(self, name, llm_config, system_message=""):
                self.name = name
                self.llm_config = llm_config
                self.system_message = system_message
            
            def generate_reply(self, messages=None, sender=None, config=None):
                return f"[{self.name}] Mock response"
        
        class GroupChat:
            def __init__(self, *args, **kwargs):
                pass
                
        class GroupChatManager:
            def __init__(self, *args, **kwargs):
                pass


class AgentWrapper(ConversableAgent):
    """Wrapper для совместимости с GroupChat"""
    
    def __init__(self, mas_agent, llm_config: Dict[str, Any]):
        super().__init__(
            name=mas_agent.name,
            llm_config=llm_config,
            system_message=getattr(mas_agent, 'system_message', f"Вы - {mas_agent.name} агент.")
        )
        self._mas_agent = mas_agent
    
    def generate_reply(self, messages=None, sender=None, config=None):
        """Делегируем генерацию ответа оригинальному агенту"""
        if hasattr(self._mas_agent, 'generate_reply'):
            return self._mas_agent.generate_reply(messages, sender, config)
        else:
            # Fallback к стандартному поведению
            return super().generate_reply(messages, sender, config)


class SimpleGroupChatManager:
    """Упрощенный GroupChat Manager без наследования"""
    
    def __init__(self, agents: Dict[str, Any], routing: Dict[str, List[str]]):
        self.agents = agents
        self.routing = routing
        self.messages = []
        
        # Создаем LLM конфигурацию
        self.llm_config = {
            "config_list": [{
                "model": "gpt-4o-mini", 
                "api_key": "dummy",  # Не используется в режиме manual
                "base_url": "https://openrouter.ai/api/v1"
            }]
        }
        
        # Создаем wrappers для совместимости
        self.wrapped_agents = {}
        for name, agent in agents.items():
            self.wrapped_agents[name] = AgentWrapper(agent, self.llm_config)
    
    def send_user_message(self, text: str) -> str:
        """Обработка пользовательского сообщения"""
        print(f"\n🔄 Получено сообщение: {text}")
        
        # Начинаем с communicator агента
        if 'communicator' in self.agents:
            response = self._route_message('communicator', text)
            return response
        else:
            return "❌ Communicator агент не найден"
    
    def _route_message(self, from_agent: str, message: str, depth: int = 0) -> str:
        """Маршрутизация сообщения между агентами"""
        if depth > 5:  # Предотвращаем бесконечную рекурсию
            return "⚠️ Превышена глубина маршрутизации"
        
        print(f"  📡 {from_agent} обрабатывает сообщение...")
        
        # Получаем список агентов для маршрутизации
        next_agents = self.routing.get(from_agent, [])
        
        if not next_agents:
            return f"✅ Сообщение обработано агентом {from_agent}"
        
        # Маршрутизируем к первому доступному агенту
        for next_agent in next_agents:
            if next_agent in self.agents:
                print(f"    ➡️ Передача {from_agent} → {next_agent}")
                return self._route_message(next_agent, message, depth + 1)
        
        return f"✅ Сообщение завершено на агенте {from_agent}"
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус системы"""
        return {
            "agents_count": len(self.agents),
            "messages_count": len(self.messages),
            "routing_rules": len(self.routing),
            "agents": list(self.agents.keys())
        }