from fastapi import APIRouter, Depends, HTTPException
from .security import rate_limit_dependency
from . import main as api_main

router = APIRouter(prefix="/api/v1/cache", tags=["cache"])


@router.get("/stats", dependencies=[Depends(rate_limit_dependency)])
async def cache_stats(current_user: dict | None = None):
    return await api_main.get_cache_stats(current_user)


@router.post("/clear", dependencies=[Depends(rate_limit_dependency)])
async def cache_clear(partial: bool = False, current_user: dict | None = None):
    return await api_main.clear_cache(partial, current_user)