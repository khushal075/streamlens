import re
import logging
from typing import Dict, Any
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)


class ContainerProcessor(BaseLogProcessor):
    """
    Handles Logs from Docker, Kubernetes, and OpenShift.
    Category: Container and Orchestration Logs
    """

    # CRI (Container Runtime Interface) format used by modern K8s
    # Format: 2026-04-04T15:24:25.12345Z <stream> <flag> <content>
    CRI_PATTERN = re.compile(
        r'(?P<kube_time>\S+)\s+(?P<stream>stdout|stderr)\s+(?P<flag>\S+)\s+(?P<log_message>.*)'
    )

    def process(self, raw_data: str) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_container_log")

        try:
            match = self.CRI_PATTERN.match(raw_data)
            if match:
                groups = match.groupdict()
                stream_type = groups['stream']

                return {
                    "timestamp": self.get_utc_now(),
                    "level": "INFO" if stream_type == "stdout" else "ERROR",
                    "message": groups['log_message'],
                    "metadata": {
                        "stream": stream_type,
                        "runtime_timestamp": groups['kube_time'],
                        "is_partial": groups['flag'] == 'P',  # 'P' for Partial, 'F' for Full
                        "parser": "k8s_cri_v1"
                    }
                }
        except Exception as e:
            logger.error(f"ContainerProcessor Regex Error: {e}")
            return self._create_fallback(raw_data, "container_parse_exception")

        # Fallback for simple Docker JSON logs or raw strings
        return {
            "timestamp": self.get_utc_now(),
            "level": "INFO",
            "message": raw_data,
            "metadata": {"parser": "generic_container_log"}
        }