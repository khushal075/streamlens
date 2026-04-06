import re
import logging
from typing import Dict, Any
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)

class SecurityProcessor(BaseLogProcessor):
    """
    Handles Logs from Authentication systems, SIEMs, and Scanners.
    Category: Security Logs (Okta, Active Directory, SSH, Auth0)
    """

    # Common patterns for security events
    AUTH_PATTERNS = [
        r'(?P<action>login|logout|failed|success|denied)',
        r'user[:\s=](?P<user>\S+)',
        r'from[:\s=](?P<source_ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',
        r'port\s+(?P<port>\d+)'
    ]

    def process(self, raw_data: str) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_security_log")

        try:
            metadata = {"parser": "security_v1"}
            message_lower = raw_data.lower()

            # 1. Simple Keyword Extraction (Heuristic)
            for pattern in self.AUTH_PATTERNS:
                match = re.search(pattern, message_lower)
                if match:
                    metadata.update(match.groupdict())

            # 2. Determine Severity
            # Security failures/denies are always WARNING or ERROR
            level = "INFO"
            if any(word in message_lower for word in ["fail", "deny", "unauthorized", "refused"]):
                level = "WARNING"
            if "critical" in message_lower or "attack" in message_lower:
                level = "ERROR"

            return {
                "timestamp": self.get_utc_now(),
                "level": level,
                "message": raw_data,
                "metadata": {
                    **metadata,
                    "is_security_event": True,
                    "event_type": "authentication" if "user" in metadata else "security_audit"
                }
            }

        except Exception as e:
            logger.error(f"SecurityProcessor Parse Error: {e}")
            return self._create_fallback(raw_data, "security_parse_exception")