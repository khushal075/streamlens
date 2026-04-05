from .base import SystemBase
from typing import Dict, Any


class SysLogProcessor(SystemBase):
    """
    Child: Specific logic for Auth, Cron, Kernel, and SSH.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Get the Syslog headers from Parent
        sys_meta = self.extract_syslog_metadata(raw_message)

        # 2. Logic: Identify Critical System States
        msg_upper = str(raw_message).upper()
        event_category = "GENERAL"

        if "OOM-KILLER" in msg_upper or "OUT OF MEMORY" in msg_upper:
            event_category = "MEMORY_CRITICAL"
        elif "DISK" in msg_upper and ("FULL" in msg_upper or "ERROR" in msg_upper):
            event_category = "STORAGE_CRITICAL"
        elif "SEGFAULT" in msg_upper or "STACK TRACE" in msg_upper:
            event_category = "APPLICATION_CRASH"

        return {
            **sys_meta,
            "event_category": event_category,
            "is_system_error": event_category != "GENERAL" or "ERROR" in msg_upper
        }