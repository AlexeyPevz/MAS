from typing import Optional
from ..schemas import SystemMetrics
import os
import time

_start_time = time.time()


async def dashboard(current_user: Optional[dict] = None):
	uptime_seconds = int(time.time() - _start_time)
	return SystemMetrics(
		total_messages=0,
		active_agents=0,
		uptime=f"{uptime_seconds}s",
		memory_usage=None,
		cpu_usage=None,
	)