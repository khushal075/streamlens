from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class LogEnvelope(BaseModel):
    """
    The 'Contract' for all logs moving through StreamLens.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str  # e.g., "nginx", "iot-sensor"
    service_name: str  # e.g., "auth-api"
    raw_payload: str  # The unparsed log string

    # Metadata: Extra info like region, container_id, etc.
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Attributes: This is where Processors store the PARSED data
    attributes: Optional[Dict[str, Any]] = None