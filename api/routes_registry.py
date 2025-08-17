from fastapi import APIRouter, HTTPException, Depends
from .security import auth_user_dependency
from .services import registry as registry_service
from .security import require_permission

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


@router.get("/tools")
async def tools():
    return await registry_service.list_tools()


@router.get("/workflows")
async def workflows():
    return await registry_service.list_workflows()


@router.get("/apps")
async def apps():
    return await registry_service.list_apps()


@router.get("/instances")
async def instances():
    raise HTTPException(status_code=501, detail="Instances registry not implemented")


@router.post("/tools/{name}/rollback")
@require_permission("admin")
async def tool_rollback(name: str, target_version: int | None = None, current_user: dict = Depends(auth_user_dependency)):
    return await registry_service.rollback_tool(name, target_version, current_user)


@router.post("/workflows/{key}/rollback")
@require_permission("admin")
async def wf_rollback(key: str, target_version: int | None = None, current_user: dict = Depends(auth_user_dependency)):
    return await registry_service.rollback_workflow(key, target_version, current_user)


@router.post("/apps/{key}/rollback")
@require_permission("admin")
async def app_rollback(key: str, target_version: int | None = None, current_user: dict = Depends(auth_user_dependency)):
    return await registry_service.rollback_app(key, target_version, current_user)