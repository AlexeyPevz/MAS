from fastapi import APIRouter
from . import main as api_main

router = APIRouter(prefix="/api/v1", tags=["misc"])


@router.get("/projects")
async def projects():
    return await api_main.get_projects()


@router.get("/logs")
async def logs(level: str = "INFO", limit: int = 100):
    return await api_main.get_logs(level, limit)