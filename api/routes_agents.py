from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .schemas import AgentStatus, AgentProfile
from .security import rate_limit_dependency
from .integration import mas_integration
from .services.agents import get_agents_service
import logging

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
logger = logging.getLogger(__name__)

# Initialize agents service
agents_service = get_agents_service(mas_integration)


@router.get("/status")
async def get_agents_status():
    """Получение статуса всех агентов"""
    try:
        # Initialize service if needed
        await agents_service.initialize()
        
        # Get status through service
        return agents_service.get_agent_status()
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса агентов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles", response_model=List[AgentProfile])
async def get_agent_profiles():
    """Получение профилей агентов для визуализации"""
    try:
        # Initialize service if needed
        await agents_service.initialize()
        
        # Get profiles through service
        return agents_service.get_agent_profiles()
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения профилей агентов: {e}")
        return []