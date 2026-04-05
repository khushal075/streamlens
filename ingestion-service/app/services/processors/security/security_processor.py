from .base import SecurityBase
from typing import Dict, Any


class SecurityProcessor(SecurityBase):
    """
    Child: Specific logic for Okta, Active Directory, and SIEM logs.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Use Parent to get Identity/Outcome
        sec_meta = self.extract_security_context(raw_message)

        # 2. Logic: Determine Event Type and Severity
        msg_upper = str(raw_message).upper()
        event_type = "GENERAL_AUDIT"
        severity = "INFO"

        if "LOGIN" in msg_upper or "AUTH" in msg_upper:
            event_type = "AUTHENTICATION"
            if sec_meta["is_failure"]:
                severity = "HIGH"  # Potential Brute Force
        elif "PASSWORD" in msg_upper or "RESET" in msg_upper:
            event_type = "CREDENTIAL_MANAGEMENT"
            severity = "MEDIUM"
        elif "DELETE" in msg_upper or "REMOVE" in msg_upper:
            event_type = "RESOURCE_DELETION"
            severity = "CRITICAL"

        return {
            **sec_meta,
            "event_type": event_type,
            "severity": severity,
            "vendor": "okta" if "OKTA" in msg_upper else "active_directory" if "AD" in msg_upper else "generic_security"
        }