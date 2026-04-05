from .base import IntegrationBase
from typing import Dict, Any


class ThirdPartyProcessor(IntegrationBase):
    """
    Child: Specific logic for Stripe, Twilio, SendGrid, and generic Webhooks.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Extract API Metadata from Parent
        api_meta = self.extract_integration_meta(raw_message)

        # 2. Logic: Determine Vendor and Impact
        msg_lower = str(raw_message).lower()
        vendor = "generic_webhook"
        impact = "LOW"

        if "stripe" in msg_lower or "ch_" in msg_lower:
            vendor = "stripe"
            if "charge.failed" in msg_lower or "refund" in msg_lower:
                impact = "HIGH"  # Financial Impact
        elif "twilio" in msg_lower or "sms" in msg_lower:
            vendor = "twilio"
            if "undelivered" in msg_lower or "failed" in msg_lower:
                impact = "MEDIUM"  # Communication Impact
        elif "sendgrid" in msg_lower or "email" in msg_lower:
            vendor = "sendgrid"

        return {
            **api_meta,
            "vendor": vendor,
            "business_impact": impact,
            "is_test_event": not api_meta["is_live_mode"]
        }