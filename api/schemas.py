from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="Message text")
    user_id: Optional[str] = Field(default="api_user", pattern=r'^[a-zA-Z0-9_-]+$', max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    response: str
    timestamp: float
    agent: Optional[str] = None
    flow_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class AgentStatus(BaseModel):
    name: str
    status: str
    last_activity: Optional[datetime] = None
    message_count: int = 0


class SystemMetrics(BaseModel):
    total_messages: int
    active_agents: int
    uptime: str
    memory_usage: Optional[str] = None
    cpu_usage: Optional[float] = None


class ProjectInfo(BaseModel):
    id: str
    name: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class AgentProfile(BaseModel):
    id: str
    name: str
    role: str
    description: str
    capabilities: List[str] = []
    avatar: str = ""
    status: str = "active"