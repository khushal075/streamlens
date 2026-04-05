import re
from typing import Dict, Any
from ..base import BaseLogProcessor


class SystemBase(BaseLogProcessor):
    """
    Parent: Logic for OS-level Syslog (Linux, Unix, BSD).
    Focuses on Facility, Severity, and PID extraction.
    """
    # Pattern to catch the classic 'service[123]:' or 'service:' format
    SYSLOG_HEADER = re.compile(r'\b([a-zA-Z0-9\._-]+)\[?(\d+)?\]?:\s')

    def extract_syslog_metadata(self, message: str) -> Dict[str, Any]:
        """
        Utility: Extracts the Service Name and Process ID (PID).
        """
        match = self.SYSLOG_HEADER.search(message)

        return {
            "system_service": match.group(1) if match else "kernel",
            "pid": int(match.group(2)) if match and match.group(2) else None,
            "is_os_internal": "kernel" in message.lower() or "systemd" in message.lower()
        }