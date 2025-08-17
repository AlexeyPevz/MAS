from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timezone
import os
import json

router = APIRouter(prefix="/api/v1", tags=["studio"])


@router.get("/studio/logs")
async def get_studio_logs(
    level: Optional[str] = Query("INFO", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$"),
    limit: int = Query(100, ge=1, le=1000),
    component: Optional[str] = None
):
    """Получение логов Studio для отладки"""
    try:
        # Читаем логи из studio_logs если они есть
        logs_dir = "logs/studio_logs"
        if not os.path.exists(logs_dir):
            return {"logs": [], "total": 0}
        
        all_logs = []
        for filename in sorted(os.listdir(logs_dir), reverse=True)[:5]:  # Last 5 files
            if filename.endswith(".jsonl"):
                filepath = os.path.join(logs_dir, filename)
                with open(filepath, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line)
                            if level and log_entry.get("level") != level:
                                continue
                            if component and log_entry.get("component") != component:
                                continue
                            all_logs.append(log_entry)
                            if len(all_logs) >= limit:
                                break
                        except:
                            continue
                if len(all_logs) >= limit:
                    break
        
        return {"logs": all_logs[:limit], "total": len(all_logs)}
    except Exception as e:
        return {"logs": [], "total": 0, "error": str(e)}


@router.get("/visualization/flows")
async def get_visualization_flows():
    """Получение активных потоков визуализации"""
    # TODO: Implement actual flow tracking
    return {"flows": [], "total": 0}