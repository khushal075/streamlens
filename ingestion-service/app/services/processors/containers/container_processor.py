# app/services/processors/containers/container_processor.py

from typing import Dict, Any
from .base import ContainerBase

class ContainerProcessor(ContainerBase):
    def specialize(self, content: str) -> Dict[str, Any]:
        # Simple default implementation
        return {"raw_content": content}

    def process(self, log: Dict[str, Any]) -> Dict[str, Any]:
        # This is what the Factory/Worker calls
        parsed = self.parse_message(log.get("message", ""))
        log["metadata"].update(parsed)
        return log