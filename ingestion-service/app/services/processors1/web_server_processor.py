import re
import logging
from typing import Dict, Any
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)


class WebServerProcessor(BaseLogProcessor):
    """
    Handles Application Logs from Web Servers (Nginx, Apache, etc.)
    Category: Application Logs
    """

    # Combined Log Format Regex (Standard for Nginx/Apache)
    # Example: 127.0.0.1 - - [04/Apr/2026:15:14:57 +0000] "GET /api/v1/data HTTP/1.1" 200 452
    WEB_PATTERN = re.compile(
        r'(?P<ip>\S+)\s+\S+\s+\S+\s+\[(?P<timestamp>.*?)\]\s+'
        r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>\S+)"\s+'
        r'(?P<status>\d+)\s+(?P<size>\d+)'
    )

    def process(self, raw_data: str) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_input")

        try:
            match = self.WEB_PATTERN.match(raw_data)
            if match:
                groups = match.groupdict()
                status_code = int(groups['status'])

                return {
                    "timestamp": self.get_utc_now(),  # Real-time ingestion time
                    "level": "INFO" if status_code < 400 else "ERROR",
                    "message": f"{groups['method']} {groups['path']}",
                    "metadata": {
                        "client_ip": groups['ip'],
                        "http_status": status_code,
                        "response_size_bytes": int(groups['size']),
                        "protocol": groups['protocol'],
                        "raw_timestamp": groups['timestamp'],  # Original log time
                        "parser": "web_server_combined"
                    }
                }
        except Exception as e:
            logger.error(f"WebProcessor Regex Error: {e}")
            return self._create_fallback(raw_data, "regex_exception")

        # If it doesn't match the web pattern, treat it as a generic application log
        return {
            "timestamp": self.get_utc_now(),
            "level": "INFO",
            "message": raw_data,
            "metadata": {"parser": "generic_app_log"}
        }