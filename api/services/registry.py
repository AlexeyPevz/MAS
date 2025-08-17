from .. import main as api_main
from fastapi import HTTPException


async def list_tools():
    return await api_main.registry_tools()


async def list_workflows():
    return await api_main.registry_workflows()


async def list_apps():
    return await api_main.registry_apps()


async def rollback_tool(name: str, target_version: int | None, current_user: dict):
    return await api_main.registry_tool_rollback(name, target_version, current_user)


async def rollback_workflow(key: str, target_version: int | None, current_user: dict):
    return await api_main.registry_workflow_rollback(key, target_version, current_user)


async def rollback_app(key: str, target_version: int | None, current_user: dict):
    return await api_main.registry_app_rollback(key, target_version, current_user)