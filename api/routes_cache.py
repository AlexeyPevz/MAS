from fastapi import APIRouter, Depends
from .security import rate_limit_dependency
from .services import cache as cache_service

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


@router.get("/stats", dependencies=[Depends(rate_limit_dependency)])
async def cache_stats(current_user: dict | None = None):
    return await cache_service.get_stats(current_user)


@router.post("/clear", dependencies=[Depends(rate_limit_dependency)])
async def cache_clear(partial: bool = False, current_user: dict | None = None):
    return await cache_service.clear(partial, current_user)