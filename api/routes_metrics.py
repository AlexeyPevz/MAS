from fastapi import APIRouter, Depends
from .schemas import SystemMetrics
from .security import rate_limit_dependency, auth_user_dependency
from . import main as api_main

router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics/dashboard", response_model=SystemMetrics, dependencies=[Depends(rate_limit_dependency)])
async def dashboard(current_user: dict | None = None):
	return await api_main.get_dashboard_metrics(current_user)