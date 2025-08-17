from fastapi import APIRouter
from .services import misc as misc_service

router = APIRouter(prefix="/api/v1", tags=["misc"])


@router.get("/projects")
async def projects():
    return await misc_service.get_projects()


@router.get("/logs")
async def logs(level: str = "INFO", limit: int = 100):
    return await misc_service.get_logs(level, limit)