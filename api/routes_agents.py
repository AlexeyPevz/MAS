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
    # TODO: Implement actual agent profiles from MAS
    return []