from typing import Optional
from .. import main as api_main


async def dashboard(current_user: Optional[dict] = None):
    return await api_main.get_dashboard_metrics(current_user)