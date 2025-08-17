from fastapi import APIRouter, Depends
from .security import rate_limit_dependency
from .services import federation as federation_service

router = APIRouter(prefix="/api/v1/federation", tags=["federation"])


@router.get("/status", dependencies=[Depends(rate_limit_dependency)])
async def status():
    return await federation_service.get_status()


@router.post("/join", dependencies=[Depends(rate_limit_dependency)])
async def join(hub_endpoint: str, specialization: list[str]):
    return await federation_service.join(hub_endpoint, specialization)


@router.post("/sync", dependencies=[Depends(rate_limit_dependency)])
async def sync():
    return await federation_service.sync()


@router.post("/receive_knowledge")
async def receive_knowledge(packet: dict):
    return await federation_service.receive_knowledge(packet)


@router.post("/request_knowledge")
async def request_knowledge(request: dict):
    return await federation_service.request_knowledge(request)