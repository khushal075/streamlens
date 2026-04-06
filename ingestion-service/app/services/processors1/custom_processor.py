import orjson
import re
import logging
from typing import Dict, Any, Union
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)

class CustomProcessor(BaseLogProcessor):
    """
    The 'Swiss Army Knife' for internal developer logs.
    Category: Custom Application Logs (Internal microservices, scripts)
    """

    # Matches bracketed tags often used in custom logs: [MY-APP] [MODULE-A]
    TAG_PATTERN = re.compile(r'\[(?P<tag>[A-Z0-9_\-]+)\]')

    def process(self, raw_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_custom_payload")

        metadata = {"parser": "custom_smart_v1"}

        # 1. Try JSON First (Modern apps use JSON)
        try:
            if isinstance(raw_data, (str, bytes)):
                data = orjson.loads(raw_data)
                # If successful, treat as structured JSON
                return {
                    "timestamp": data.get("timestamp") or self.get_utc_now(),
                    "level": str(data.get("level", "INFO")).upper(),
                    "message": data.get("message") or data.get("msg") or str(data),
                    "metadata": {**data, **metadata}
                }
        except Exception:
            pass # Not JSON, move to string parsing

        # 2. String Parsing: Extract Tags and Metadata
        str_data = str(raw_data)
        tags = self.TAG_PATTERN.findall(str_data)
        if tags:
            metadata["app_tags"] = tags

        # 3. Heuristic Level Detection
        level = "INFO"
        upper_msg = str_data.upper()
        if "ERROR" in upper_msg or "EXCEPTION" in upper_msg:
            level = "ERROR"
        elif "WARN" in upper_msg:
            level = "WARNING"

        return {
            "timestamp": self.get_utc_now(),
            "level": level,
            "message": str_data,
            "metadata": metadata
        }