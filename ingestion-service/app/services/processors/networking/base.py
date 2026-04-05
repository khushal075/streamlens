import re
from typing import Dict, Any, List
from ..base import BaseLogProcessor


class NetworkBase(BaseLogProcessor):
    """
    Parent: Shared utilities for all Networking gear (Firewalls, Routers, etc.)
    Handles high-performance Regex for IP/Port extraction.
    """
    # Pre-compile regex for performance (Thread-safe)
    IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    PORT_PATTERN = re.compile(r'\b(?::|port\s)(\d{1,5})\b', re.IGNORECASE)

    def extract_network_metadata(self, message: str) -> Dict[str, Any]:
        """
        Utility: Automatically finds IPs and Ports in a raw string.
        """
        ips = self.IP_PATTERN.findall(message)
        ports = self.PORT_PATTERN.findall(message)

        return {
            "source_ip": ips[0] if len(ips) > 0 else None,
            "dest_ip": ips[1] if len(ips) > 1 else None,
            "source_port": int(ports[0]) if len(ports) > 0 else None,
            "dest_port": int(ports[1]) if len(ports) > 1 else None,
            "ip_count": len(ips)
        }

    @abstractmethod
    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        """Child classes (Cisco/Fortigate) will implement this."""
        pass