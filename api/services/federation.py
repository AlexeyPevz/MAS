from typing import Any, Dict, List
from .. import main as api_main


async def get_status() -> Dict[str, Any]:
    return api_main.federation_hub.get_federation_status()  # type: ignore[attr-defined]


async def join(hub_endpoint: str, specialization: List[str]) -> Dict[str, Any]:
    success = await api_main.federation_hub.join_federation(hub_endpoint, specialization)  # type: ignore[attr-defined]
    return {"success": success}


async def sync() -> Dict[str, Any]:
    stats = await api_main.federation_hub.sync_with_federation()  # type: ignore[attr-defined]
    return stats


async def receive_knowledge(packet: Dict[str, Any]) -> Dict[str, str]:
    # Store in cache
    api_main.federation_hub.knowledge_cache[packet["packet_id"]] = packet  # type: ignore[attr-defined]
    return {"status": "received"}


async def request_knowledge(request: Dict[str, Any]) -> List[Dict[str, Any]]:
    packets = api_main.federation_hub.prepare_knowledge_for_sharing(request.get("knowledge_domain", "general"))  # type: ignore[attr-defined]
    return [p.__dict__ for p in packets[:10]]