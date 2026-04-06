from abc import ABC, abstractmethod
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Union, List


class BaseLogProcessor(ABC):
    """
    The Grandfather Class.
    Handles Batching, Metadata, and Fallbacks.
    """

    @abstractmethod
    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        """
        The 'Hook'.
        Children like NginxProcessor only implement this.
        """
        pass

    def process_batch(self, log_envelope: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        The Template Method.
        This handles the loop and the 'Shared' fields for all 10 categories.
        """
        processed_logs = []
        tenant_id = log_envelope.get("tenant_id", "unknown")
        service = log_envelope.get("service", "generic")
        source = log_envelope.get("source", "raw")

        for entry in log_envelope.get("logs", []):
            raw_msg = entry.get("message", "")

            # 1. Validation logic (from your current code)
            if not self._is_valid(raw_msg):
                processed_logs.append(self._create_fallback(raw_msg, "Empty or Null input"))
                continue

            try:
                # 2. Call the child's specialized regex
                extracted_data = self.parse_message(raw_msg)

                # 3. Standardization (The Senior 'Contract')
                processed_logs.append({
                    "log_id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "service": service,
                    "source": source,
                    "timestamp": entry.get("timestamp") or self.get_utc_now().timestamp(),
                    "level": entry.get("level", "INFO"),
                    "message": raw_msg,
                    "attributes": extracted_data,  # The Dynamic JSON part
                    "metadata": entry.get("metadata", {})
                })
            except Exception as e:
                # 4. Fallback (Ensures zero data loss)
                processed_logs.append(self._create_fallback(raw_msg, f"Parsing Error: {str(e)}"))

        return processed_logs

    def get_utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _is_valid(self, raw_data: Any) -> bool:
        return bool(raw_data and str(raw_data).strip())

    def _create_fallback(self, raw_data: Any, reason: str) -> Dict[str, Any]:
        return {
            "log_id": str(uuid.uuid4()),
            "timestamp": self.get_utc_now().timestamp(),
            "level": "ERROR",
            "message": str(raw_data),
            "attributes": {"error": reason, "raw_captured": True}
        }