import orjson
import logging
from typing import Dict, Any, Union
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)


class ThirdPartyProcessor(BaseLogProcessor):
    """
    Handles Logs from External Services (Stripe, Twilio, SendGrid).
    Category: Third-Party Service Logs
    """

    def process(self, raw_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_webhook_payload")

        try:
            # 1. Parse JSON
            data = raw_data
            if isinstance(raw_data, (str, bytes)):
                data = orjson.loads(raw_data)

            # 2. Extract Vendor Intelligence
            # Stripe uses 'type', Twilio uses 'SmsStatus', etc.
            event_type = (
                    data.get("type") or
                    data.get("event") or
                    data.get("SmsStatus") or
                    "external_api_call"
            )

            # Identify the specific resource (e.g., customer_id, message_sid)
            external_id = (
                    data.get("id") or
                    data.get("data", {}).get("object", {}).get("id") or
                    data.get("MessageSid")
            )

            return {
                "timestamp": self.get_utc_now(),
                "level": self._check_failure(data, event_type),
                "message": f"ThirdParty Event: {event_type}",
                "metadata": {
                    "external_id": str(external_id) if external_id else "unknown",
                    "event_type": event_type,
                    "payload_size": len(str(data)),
                    "parser": "third_party_json_v1",
                    "full_payload": data  # Crucial for debugging external issues
                }
            }

        except Exception as e:
            logger.error(f"ThirdPartyProcessor Error: {e}")
            return self._create_fallback(raw_data, "webhook_parse_exception")

    def _check_failure(self, data: Dict, event: str) -> str:
        """Determines if the external service reported a failure."""
        fail_keywords = ["failed", "error", "denied", "rejected", "undelivered"]
        if any(word in event.lower() for word in fail_keywords):
            return "ERROR"
        return "INFO"