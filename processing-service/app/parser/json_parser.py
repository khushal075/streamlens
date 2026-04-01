# app/parser/json_parser.py
from typing import Any, Dict
from pydantic import BaseModel, ValidationError

class RawLog(BaseModel):
    tenant_id: str
    service: str
    timestamp: int
    message: str
    metadata: Dict[str, Any] = {}

def parse_json_log(log_data: Dict[str, Any]) -> RawLog | None:
    try:
        return RawLog(**log_data)
    except ValidationError as e:
        print(f"[Parser] Validation failed: {e}")
        return None