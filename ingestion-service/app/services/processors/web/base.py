import re
from typing import Dict, Any
from ..base import BaseLogProcessor


class WebBase(BaseLogProcessor):
    """
    Parent: Standardized HTTP log parsing (Nginx, Apache, Node.js).
    """
    # Pattern for [METHOD] /path/to/resource HTTP/1.1
    HTTP_PATTERN = re.compile(r'"(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s+([^\s?]+)[^"]*"', re.IGNORECASE)
    # Pattern for 3-digit Status Codes (200, 404, 500)
    STATUS_PATTERN = re.compile(r'\s([1-5]\d{2})\s')

    def extract_web_metrics(self, message: str) -> Dict[str, Any]:
        """
        Utility: Extracts Method, Path, and Status Code.
        """
        http_match = self.HTTP_PATTERN.search(message)
        status_match = self.STATUS_PATTERN.search(message)

        return {
            "method": http_match.group(1).upper() if http_match else "UNKNOWN",
            "path": http_match.group(2) if http_match else "/",
            "status_code": int(status_match.group(1)) if status_match else 0
        }