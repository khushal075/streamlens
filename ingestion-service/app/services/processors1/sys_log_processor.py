import re
import logging
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)

class SysLogProcessor(BaseLogProcessor):
    # Common RFC3164 Syslog Regex
    SYSLOG_PATTERN = re.compile(
        r'<(?P<priority>\d+)> (?P<timestamp>\w{3}\s+\d+\s\d+:\d+:\d+) (?P<hostname>\S+) (?P<tag>\S+): (?P<message>.*)'
    )

    def process(self, raw_data: str) -> dict:
        """
        Processes raw syslog strings.
        Handles NoneType or empty strings gracefully to prevent worker crashes.
        """
        # 1. Null/Empty Safety Check
        if not raw_data or not isinstance(raw_data, (str, bytes)):
            return self._fallback_result(str(raw_data), error="invalid_input_type")

        # 2. Regex Matching
        try:
            match = self.SYSLOG_PATTERN.match(raw_data)
            if match:
                groups = match.groupdict()
                return {
                    "timestamp": self.get_utc_now(),  # In production, use a parser for groups['timestamp']
                    "level": self._map_priority(groups.get('priority', '6')),
                    "message": groups.get('message', ''),
                    "metadata": {
                        "hostname": groups.get('hostname', 'unknown'),
                        "tag": groups.get('tag', 'untagged'),
                        "parser": "syslog_rfc3164"
                    }
                }
        except Exception as e:
            logger.error(f"Unexpected error in SysLogProcessor: {e}")
            return self._fallback_result(raw_data, error="internal_processor_error")

        # 3. Fallback for non-matching strings
        return self._fallback_result(raw_data, error="regex_mismatch")

    def _fallback_result(self, raw_data: str, error: str) -> dict:
        """Helper to standardize failed parsing results."""
        return {
            "timestamp": self.get_utc_now(),
            "level": "UNKNOWN",
            "message": raw_data,
            "metadata": {
                "parsing_error": error,
                "raw_captured": "true"
            }
        }

    def _map_priority(self, priority: str):
        try:
            p = int(priority)
            if p <= 3: return "ERROR"
            if p == 4: return "WARNING"
            return "INFO"
        except (ValueError, TypeError):
            return "INFO"