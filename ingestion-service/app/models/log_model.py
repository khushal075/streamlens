"""
Log Models
----------
Role: Data Validation and Type Safety.
Pattern: Data Transfer Object (DTO).
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class LogEntry(BaseModel):
    """
    Represents a single log event sent by the client.
    """
    message: str = Field(..., description="The raw log string (e.g., Nginx access line)")
    timestamp: int = Field(..., description="Unix timestamp of the event")
    level: str = Field(default="INFO", description="Log severity level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "GET /api/v1/users 200",
                "timestamp": 1712314200,
                "level": "INFO",
                "metadata": {"user_id": "123"}
            }
        }
    )

class LogRequest(BaseModel):
    """
    The wrapper for a batch ingestion request.
    """
    tenant_id: str = Field(..., min_length=1)
    service: str = Field(..., min_length=1)
    # This determines which Strategy (Processor) the worker picks
    source: str = Field(default="generic", description="Source type (e.g., nginx, syslog, cloud)")
    logs: List[LogEntry] = Field(..., min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tenant_id": "acme_corp",
                "service": "billing_api",
                "source": "web",
                "logs": []
            }
        }
    )