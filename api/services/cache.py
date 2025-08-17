from typing import Optional
from .. import main as api_main


async def get_stats(current_user: Optional[dict] = None):
    return await api_main.get_cache_stats(current_user)


async def clear(partial: bool = False, current_user: Optional[dict] = None):
    return await api_main.clear_cache(partial, current_user)