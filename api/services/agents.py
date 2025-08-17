"""
Agents service for handling agent operations
"""
from typing import Dict, Any, List
from .base import BaseService
from core.interfaces import IMessageProcessor
from config.config_loader import load_config
from ..schemas import AgentStatus, AgentProfile


class AgentsService(BaseService):
    """Service for handling agent operations"""
    
    def __init__(self, message_processor: IMessageProcessor):
        super().__init__()
        self.message_processor = message_processor
        self.config = None
    
    async def _setup(self) -> None:
        """Initialize agents service resources"""
        self.config = load_config()
    
    def get_agent_status(self) -> Dict[str, List[AgentStatus]]:
        """Get status of all agents"""
        try:
            # Get status from MAS system
            agents_data = self.message_processor.get_agent_status()
            
            # Convert to AgentStatus objects
            agent_statuses = []
            for name, info in agents_data.items():
                status = AgentStatus(
                    name=name,
                    status="active" if info.get("active", False) else "inactive",
                    last_activity=info.get("last_activity"),
                    message_count=info.get("message_count", 0)
                )
                agent_statuses.append(status)
            
            return {"agents": agent_statuses, "total": len(agent_statuses)}
            
        except Exception as e:
            self.logger.error(f"Error getting agent status: {e}")
            return {"agents": [], "total": 0}
    
    def get_agent_profiles(self) -> List[AgentProfile]:
        """Get agent profiles for visualization"""
        try:
            if not self.config:
                self.config = load_config()
            
            agents_config = self.config.get('agents', {})
            
            profiles = []
            for agent_name, agent_info in agents_config.items():
                profile = AgentProfile(
                    id=agent_name,
                    name=agent_name.replace('_', ' ').title(),
                    role=agent_info.get('role', 'Assistant'),
                    description=agent_info.get('description', f'{agent_name} agent'),
                    capabilities=agent_info.get('capabilities', []),
                    avatar=f"/assets/agents/{agent_name}.png",
                    status="active"
                )
                profiles.append(profile)
            
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error getting agent profiles: {e}")
            return []
    
    def get_agent_metrics(self, agent_name: str) -> Dict[str, Any]:
        """Get detailed metrics for specific agent"""
        try:
            all_status = self.message_processor.get_agent_status()
            agent_info = all_status.get(agent_name, {})
            
            return {
                "name": agent_name,
                "metrics": {
                    "message_count": agent_info.get("message_count", 0),
                    "success_rate": agent_info.get("success_rate", 0.0),
                    "avg_response_time": agent_info.get("avg_response_time", 0.0),
                    "last_activity": agent_info.get("last_activity")
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting agent metrics: {e}")
            return {"name": agent_name, "metrics": {}}


# Singleton instance
_agents_service = None


def get_agents_service(message_processor: IMessageProcessor) -> AgentsService:
    """Get or create agents service instance"""
    global _agents_service
    if _agents_service is None:
        _agents_service = AgentsService(message_processor)
    return _agents_service