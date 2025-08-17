from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .schemas import AgentStatus, AgentProfile
from .security import rate_limit_dependency
from .integration import mas_integration
import logging

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
logger = logging.getLogger(__name__)


@router.get("/status")
async def get_agents_status():
    """Получение статуса всех агентов"""
    try:
        # Получаем статус из MAS системы
        agents = mas_integration.get_agent_status()
        
        # Преобразуем в список AgentStatus
        agent_statuses = []
        for name, info in agents.items():
            status = AgentStatus(
                name=name,
                status="active" if info.get("active", False) else "inactive",
                last_activity=info.get("last_activity"),
                message_count=info.get("message_count", 0)
            )
            agent_statuses.append(status)
        
        return {"agents": agent_statuses, "total": len(agent_statuses)}
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса агентов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles", response_model=List[AgentProfile])
async def get_agent_profiles():
    """Получение профилей агентов для визуализации"""
    try:
        # Get agent profiles from configuration
        from config.config_loader import load_config
        config = load_config()
        agents_config = config.get('agents', {})
        
        profiles = []
        for agent_name, agent_info in agents_config.items():
            profile = AgentProfile(
                id=agent_name,
                name=agent_name.replace('_', ' ').title(),
                role=agent_info.get('role', 'Assistant'),
                description=agent_info.get('description', f'{agent_name} agent'),
                capabilities=agent_info.get('capabilities', []),
                avatar=f"/assets/agents/{agent_name}.png",  # Default avatar path
                status="active"
            )
            profiles.append(profile)
        
        return profiles
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения профилей агентов: {e}")
        return []