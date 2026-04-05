from .base import NetworkBase
from typing import Dict, Any


class NetworkProcessor(NetworkBase):
    """
    Child: Specific logic for Cisco, Fortigate, and generic Routers.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Use the Parent logic to get IPs/Ports automatically
        net_meta = self.extract_network_metadata(raw_message)

        # 2. Add Vendor-specific logic (Action & Protocol)
        action = "DENY" if any(x in raw_message.upper() for x in ["DROP", "DENY", "BLOCK"]) else "ALLOW"
        protocol = "TCP" if "TCP" in raw_message.upper() else "UDP" if "UDP" in raw_message.upper() else "OTHER"

        return {
            **net_meta,
            "action": action,
            "protocol": protocol,
            "vendor_type": "firewall" if "ASA" in raw_message or "FG" in raw_message else "router"
        }