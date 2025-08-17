from .. import main as api_main


async def get_projects():
    return await api_main.get_projects()


async def get_logs(level: str = "INFO", limit: int = 100):
    return await api_main.get_logs(level, limit)