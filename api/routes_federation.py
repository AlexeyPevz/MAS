from fastapi import APIRouter, Depends
from .security import rate_limit_dependency
from . import main as api_main

router = APIRouter(prefix="/api/v1/federation", tags=["federation"])


@router.get("/status", dependencies=[Depends(rate_limit_dependency)])
async def status():
    return await api_main.get_federation_status()


@router.post("/join", dependencies=[Depends(rate_limit_dependency)])
async def join(hub_endpoint: str, specialization: list[str]):
    return await api_main.join_federation(hub_endpoint, specialization)


@router.post("/sync", dependencies=[Depends(rate_limit_dependency)])
async def sync():
    return await api_main.sync_federation()