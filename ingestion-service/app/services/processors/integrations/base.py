import json
from typing import Dict, Any
from ..base import BaseLogProcessor


class IntegrationBase(BaseLogProcessor):
    """
    Parent: Logic for Third-Party APIs and Webhooks (Stripe, Twilio).
    Focuses on Event IDs, Signatures, and Payload extraction.
    """

    def extract_integration_meta(self, raw_message: str) -> Dict[str, Any]:
        """
        Utility: Attempts to find common API event identifiers.
        """
        try:
            data = json.loads(raw_message) if isinstance(raw_message, str) else raw_message

            return {
                "event_id": data.get("id") or data.get("event_id") or data.get("sid"),
                "api_version": data.get("api_version") or data.get("version", "v1"),
                "is_live_mode": data.get("livemode", True)  # Common in Stripe/Payment APIs
            }
        except (json.JSONDecodeError, AttributeError):
            return {"event_id": "none", "api_version": "unknown", "is_live_mode": False}