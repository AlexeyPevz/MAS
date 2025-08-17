from fastapi import APIRouter, HTTPException
from . import main as api_main

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


@router.get("/tools")
async def tools():
	return await api_main.registry_tools()


@router.get("/workflows")
async def workflows():
	return await api_main.registry_workflows()


@router.get("/apps")
async def apps():
	return await api_main.registry_apps()


@router.get("/instances")
async def instances():
	raise HTTPException(status_code=501, detail="Instances registry not implemented")