from fastapi import APIRouter, Depends
from .schemas import SystemMetrics
from .security import rate_limit_dependency
from .services import metrics as metrics_service

router = APIRouter(prefix="/api/v1", tags=["metrics"])


@router.get("/metrics/dashboard", response_model=SystemMetrics, dependencies=[Depends(rate_limit_dependency)])
async def dashboard(current_user: dict | None = None):
    return await metrics_service.dashboard(current_user)