import re
from abc import abstractmethod
from typing import Dict, Any, List, Optional
from ..base import BaseLogProcessor  # Assuming your Processor tree is still here
from app.services.processors.networking.base import BaseLogProcessor

class NetworkBase(BaseLogProcessor):
    """
    Parent: Shared utilities for all Networking gear (Firewalls, Routers, etc.)
    Handles high-performance Regex for IP/Port extraction.
    """
    # ⚡ Pre-compile regex at class level for thread-safety and speed
    # Matches IPv4 addresses
    IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    # Matches ports (e.g., ":443" or "port 80")
    PORT_PATTERN = re.compile(r'\b(?::|port\s)(\d{1,5})\b', re.IGNORECASE)

    def extract_network_metadata(self, message: str) -> Dict[str, Any]:
        """
        Utility: Automatically finds IPs and Ports in a raw string.
        Standardizes them into a format ready for ClickHouse Map(String, String).
        """
        ips = self.IP_PATTERN.findall(message)
        ports = self.PORT_PATTERN.findall(message)

        # We return a dictionary that easily merges into our LogEnvelope metadata
        return {
            "nw_src_ip": ips[0] if len(ips) > 0 else None,
            "nw_dst_ip": ips[1] if len(ips) > 1 else None,
            "nw_src_port": ports[0] if len(ports) > 0 else None,
            "nw_dst_port": ports[1] if len(ports) > 1 else None,
            "nw_ip_count": str(len(ips)) # Keep as string for ClickHouse Map compatibility
        }

    @abstractmethod
    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        """
        Child classes (Cisco/Fortigate) will implement this.
        Example: return self.extract_network_metadata(raw_message)
        """
        pass