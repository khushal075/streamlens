import logging
from typing import Dict
from .base import BaseLogProcessor
from .sys_log_processor import SysLogProcessor

from .web_server_processor import WebServerProcessor
from .cloud_log_processor import CloudLogProcessor
from .container_processor import ContainerProcessor
from .network_processor import NetworkProcessor
from .security_processor import SecurityProcessor
from .database_processor import DatabaseProcessor
from .third_party_processor import ThirdPartyProcessor
from .iot_processor import IoTProcessor
from .custom_processor import CustomProcessor


logger = logging.getLogger(__name__)


class LogProcessor:
    def __init__(self):
        """
        Registry of specialized processors.
        Each must inherit from BaseLogProcessor.
        """
        self._processors: Dict[str, BaseLogProcessor] = {
            "syslog": SysLogProcessor(),
            #"auth": SysLogProcessor(),  # Example: reuse syslog logic for auth service
            "nginx": WebServerProcessor(),  # <--- New
            "apache": WebServerProcessor(),  # <--- New
            "web_app": WebServerProcessor(),  # <--- New
            "aws": CloudLogProcessor(),
            "gcp": CloudLogProcessor(),
            "azure": CloudLogProcessor(),
            "cloudtrail": CloudLogProcessor(),

            # ------------ Containers ------------------------
            "kubernetes": ContainerProcessor(),  # Category: Containers
            "docker": ContainerProcessor(),  # Category: Containers
            "openshift": ContainerProcessor(),  # Category: Containers

            # ------------------- Network logs -------------------
            "firewall": NetworkProcessor(),  # Category: Network Devices
            "router": NetworkProcessor(),  # Category: Network Devices
            "cisco": NetworkProcessor(),  # Category: Network Devices
            "fortigate": NetworkProcessor(),  # Category: Network Devices

            "auth": SecurityProcessor(),  # Category: Security Logs
            "okta": SecurityProcessor(),  # Category: Security Logs
            "active_directory": SecurityProcessor(),
            "siem": SecurityProcessor(),

            "postgresql": DatabaseProcessor(),  # Category: Database Logs
            "mongodb": DatabaseProcessor(),  # Category: Database Logs
            "database": DatabaseProcessor(),

            "stripe": ThirdPartyProcessor(),  # Category: Third-Party
            "twilio": ThirdPartyProcessor(),  # Category: Third-Party
            "sendgrid": ThirdPartyProcessor(),  # Category: Third-Party
            "webhook": ThirdPartyProcessor(),

            "sensor": IoTProcessor(),  # Category: IoT
            "gateway": IoTProcessor(),  # Category: IoT
            "iot": IoTProcessor(),  # Category: IoT
            "telemetry": IoTProcessor(),

            # Category 10: The Custom Catch-all
            "custom": CustomProcessor(),
            "internal": CustomProcessor(),
            "app": CustomProcessor()

        }

        # Use SysLogProcessor as the default if no match is found
        self.default_processor = SysLogProcessor()

    def process(self, log_envelope: dict) -> dict:
        """
        Orchestrates the transformation of a raw log into a structured object.
        """
        # 1. Identity the source/service type
        source = log_envelope.get("source") or log_envelope.get("service") or "generic"
        source_key = source.lower()

        # 2. Select the specialist from our registry
        processor = self._processors.get(source_key, self.default_processor)

        # 3. Extract the raw message to be parsed
        raw_message = log_envelope.get("message") or ""

        # 4. Perform Polymorphic Processing
        # Because every processor follows the BaseLogProcessor contract,
        # we can safely call .process() here.
        try:
            structured_log = processor.process(raw_message)
        except Exception as e:
            logger.error(f"Critical failure in {processor.__class__.__name__}: {e}")
            # Use the base class fallback if a specific processor crashes
            structured_log = processor._create_fallback(raw_message, "processor_crash")

        # 5. Enrichment: Re-attach global context (The "Envelope" data)
        # This ensures every log in ClickHouse has these common fields
        structured_log.update({
            "tenant_id": log_envelope.get("tenant_id"),
            "service": log_envelope.get("service", "unknown"),
            "source": source,
            "ingested_at": self.default_processor.get_utc_now()
        })

        return structured_log