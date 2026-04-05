from .base import WebBase
from typing import Dict, Any


class WebProcessor(WebBase):
    """
    Child: Specific logic for Nginx, Apache, and Custom Web Apps.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Use Parent to get HTTP details
        web_meta = self.extract_web_metrics(raw_message)

        # 2. Logic: Categorize based on status code
        status = web_meta["status_code"]
        category = "SUCCESS"
        if 400 <= status < 500:
            category = "CLIENT_ERROR"
        elif status >= 500:
            category = "SERVER_ERROR"
        elif status == 0:
            category = "MALFORMED"

        # 3. Logic: Identify asset type
        path = web_meta["path"].lower()
        is_static = any(path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.ico'])

        return {
            **web_meta,
            "response_category": category,
            "request_type": "STATIC_ASSET" if is_static else "API_CALL",
            "is_error": status >= 400
        }