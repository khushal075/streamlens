import os
from typing import Dict, Any
from .base import WebBase

# Defined at module level so it's only created once in memory
STATIC_EXTENSIONS = {'.js', '.css', '.png', '.jpg', '.ico', '.svg', '.woff2'}


class WebProcessor(WebBase):
    """
    Child: Specific logic for Nginx, Apache, and Custom Web Apps.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Use Parent (WebBase) to extract core regex fields
        web_meta = self.extract_web_metrics(raw_message)

        # 2. Logic: Categorize based on status code
        status = web_meta.get("status_code", 0)
        category = "SUCCESS"

        if 400 <= status < 500:
            category = "CLIENT_ERROR"
        elif status >= 500:
            category = "SERVER_ERROR"
        elif status == 0:
            category = "MALFORMED"

        # 3. Logic: Identify asset type (High Performance Set Lookup)
        path = web_meta.get("path", "").lower()
        _, ext = os.path.splitext(path)
        is_static = ext in STATIC_EXTENSIONS

        return {
            **web_meta,
            "response_category": category,
            "request_type": "STATIC_ASSET" if is_static else "API_CALL",
            "is_error": status >= 400
        }