import logging
from typing import Dict
from .base import BaseLogProcessor

# Import the Specialists from their domain folders
from .networking import NetworkProcessor
from .containers import ContainerProcessor
from .storage import DatabaseProcessor
from .web import WebProcessor
from .cloud import CloudProcessor
from .security import SecurityProcessor
from .system import SysLogProcessor
from .integrations import ThirdPartyProcessor
from .iot import IoTProcessor
from .custom import CustomProcessor

logger = logging.getLogger(__name__)


class LogProcessorFactory:
    def __init__(self):
        """
        Registry of specialized processors.
        Each instance is created once and reused (Singleton Pattern).
        """
        # 1. Initialize the 10 Specialists
        net = NetworkProcessor()
        cont = ContainerProcessor()
        db = DatabaseProcessor()
        web = WebProcessor()
        cloud = CloudProcessor()
        sec = SecurityProcessor()
        sys = SysLogProcessor()
        api = ThirdPartyProcessor()
        iot = IoTProcessor()
        custom = CustomProcessor()

        # 2. Map source keys to the Specialists
        self._registry: Dict[str, BaseLogProcessor] = {
            # Networking
            "firewall": net, "router": net, "cisco": net, "fortigate": net,

            # Containers
            "kubernetes": cont, "docker": cont, "openshift": cont, "k8s": cont,

            # Storage
            "postgresql": db, "mongodb": db, "mysql": db, "database": db, "redis": db,

            # Web
            "nginx": web, "apache": web, "web_app": web, "ingress": web,

            # Cloud
            "aws": cloud, "gcp": cloud, "azure": cloud, "cloudtrail": cloud,

            # Security
            "auth": sec, "okta": sec, "active_directory": sec, "siem": sec, "vpn": sec,

            # System
            "syslog": sys, "kernel": sys, "cron": sys, "ssh": sys,

            # Integrations (Third-Party)
            "stripe": api, "twilio": api, "sendgrid": api, "webhook": api,

            # IoT
            "sensor": iot, "gateway": iot, "telemetry": iot, "mqtt": iot,

            # Custom / Fallback
            "custom": custom, "internal": custom, "app": custom, "generic": custom
        }

        self.default_processor = sys

    def get_processor(self, source: str) -> BaseLogProcessor:
        """
        O(1) Lookup to find the correct processor.
        """
        if not source:
            return self.default_processor

        return self._registry.get(source.lower(), self.default_processor)

    def register_processor(self, source: str, processor: BaseLogProcessor):
        """Allows dynamic registration of new log sources."""
        self._registry[source.lower()] = processor
        logger.info(f"✅ Registered new processor for source: {source}")


# Global Instance for the Kafka Worker to import
processor_factory = LogProcessorFactory()