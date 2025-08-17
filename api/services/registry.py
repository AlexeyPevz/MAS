from .. import main as api_main
from fastapi import HTTPException
from tools import multitool as mt


async def list_tools():
    return mt.list_tools()


async def list_workflows():
    return mt.list_workflows()


async def list_apps():
    return mt.list_apps()


async def rollback_tool(name: str, target_version: int | None, current_user: dict):
    ok = mt.rollback_tool(name, target_version)
    if not ok:
        raise HTTPException(status_code=404, detail="Tool or version not found")
    return {"status": "ok"}


async def rollback_workflow(key: str, target_version: int | None, current_user: dict):
    ok = mt.rollback_workflow(key, target_version)
    if not ok:
        raise HTTPException(status_code=404, detail="Workflow or version not found")
    return {"status": "ok"}


async def rollback_app(key: str, target_version: int | None, current_user: dict):
    ok = mt.rollback_app(key, target_version)
    if not ok:
        raise HTTPException(status_code=404, detail="App or version not found")
    return {"status": "ok"}