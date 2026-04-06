import re
import logging
from typing import Dict, Any
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)


class NetworkProcessor(BaseLogProcessor):
    """
    Handles Logs from Firewalls, Routers, and Switches.
    Category: Network Devices Logs (Cisco, Fortigate, Palo Alto)
    """

    # Regex to find key=value or key="value"
    # Matches: devname=FG-100D, srcip=192.168.1.1, msg="User login"
    KVP_PATTERN = re.compile(r'(?P<key>\w+)=(?P<quote>["\']?)(?P<value>.*?)(?P=quote)(?:,|\s|$)')

    def process(self, raw_data: str) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_network_log")

        try:
            # 1. Extract all Key-Value pairs
            matches = self.KVP_PATTERN.findall(raw_data)
            kvp_dict = {m[0].lower(): m[2] for m in matches}

            if kvp_dict:
                # 2. Determine Severity
                # Network logs often use 'level', 'pri', or 'severity' keys
                raw_level = kvp_dict.get('level') or kvp_dict.get('pri') or "6"

                return {
                    "timestamp": self.get_utc_now(),
                    "level": self._map_network_priority(raw_level),
                    "message": kvp_dict.get('msg') or kvp_dict.get(
                        'reason') or f"Network Event: {kvp_dict.get('action', 'Unknown')}",
                    "metadata": {
                        **kvp_dict,
                        "parser": "network_kvp_v1",
                        "device_type": kvp_dict.get('devtype', 'generic_network')
                    }
                }
        except Exception as e:
            logger.error(f"NetworkProcessor KVP Error: {e}")
            return self._create_fallback(raw_data, "network_parse_exception")

        # Fallback for simple syslog-style network logs
        return {
            "timestamp": self.get_utc_now(),
            "level": "INFO",
            "message": raw_data,
            "metadata": {"parser": "generic_network_log"}
        }

    def _map_network_priority(self, pri: str) -> str:
        """Maps numeric network priorities to standard levels."""
        try:
            p = int(pri)
            if p <= 3: return "ERROR"
            if p == 4: return "WARNING"
            return "INFO"
        except (ValueError, TypeError):
            return "INFO"