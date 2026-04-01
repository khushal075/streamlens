from pydantic import BaseModel
from typing import List, Dict, Any

class LogEntry(BaseModel):
    message: str
    timestamp: int
    level: str = "INFO"
    metadata: Dict[str, Any] = {}

class LogRequest(BaseModel):
    tenant_id: str
    service: str
    logs: List[LogEntry]