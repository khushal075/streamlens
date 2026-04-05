from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, List, Union
import uuid


class BaseLogProcessor(ABC):
    """
    The Grandfather Class.
    Handles Batching, Metadata, and Thread-Safe Validation.
    """

    @abstractmethod
    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        """The 'Hook' for children (Nginx, Cisco, etc.)"""
        pass

    def process_batch(self, log_envelope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        The Template Method.
        This is what the ThreadPoolExecutor will call.
        """
        processed_logs = []
        tenant_id = log_envelope.get("tenant_id", "system")
        source = log_envelope.get("source", "generic")

        for entry in log_envelope.get("logs", []):
            raw_msg = entry.get("message", "")

            if not self._is_valid(raw_msg):
                processed_logs.append(self._create_fallback(raw_msg, "Empty log", tenant_id))
                continue

            try:
                # Call the specialized child logic
                extracted_data = self.parse_message(raw_msg)

                processed_logs.append({
                    "log_id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "source": source,
                    "timestamp": entry.get("timestamp") or self.get_utc_now().timestamp(),
                    "message": raw_msg,
                    "attributes": extracted_data,  # Specific Regex results go here
                    "ingested_at": self.get_utc_now().isoformat()
                })
            except Exception as e:
                processed_logs.append(self._create_fallback(raw_msg, str(e), tenant_id))

        return processed_logs

    def get_utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _is_valid(self, data: Any) -> bool:
        return bool(data and str(data).strip())

    def _create_fallback(self, raw: Any, reason: str, tenant: str) -> Dict[str, Any]:
        return {
            "log_id": str(uuid.uuid4()),
            "tenant_id": tenant,
            "message": str(raw),
            "attributes": {"error": reason, "raw_captured": True},
            "timestamp": self.get_utc_now().timestamp()
        }