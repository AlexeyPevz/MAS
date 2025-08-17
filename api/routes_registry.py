from fastapi import APIRouter, HTTPException, Depends
from . import main as api_main
from .security import auth_user_dependency

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


@router.post("/tools/{name}/rollback")
async def tool_rollback(name: str, target_version: int | None = None, current_user: dict = Depends(auth_user_dependency)):
	return await api_main.registry_tool_rollback(name, target_version, current_user)


@router.post("/workflows/{key}/rollback")
async def wf_rollback(key: str, target_version: int | None = None, current_user: dict = Depends(auth_user_dependency)):
	return await api_main.registry_workflow_rollback(key, target_version, current_user)


@router.post("/apps/{key}/rollback")
async def app_rollback(key: str, target_version: int | None = None, current_user: dict = Depends(auth_user_dependency)):
	return await api_main.registry_app_rollback(key, target_version, current_user)