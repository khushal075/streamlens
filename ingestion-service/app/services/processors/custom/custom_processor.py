from .base import CustomBase
from typing import Dict, Any


class CustomProcessor(CustomBase):
    """
    Child: The 'Catch-All' Specialist.
    Used for internal app logs or when no other processor matches.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Use Parent to harvest any visible keys/tags
        discovered_tags = self.extract_generic_tags(raw_message)

        # 2. Logic: Identify if it's an Internal App log
        msg_upper = str(raw_message).upper()
        is_internal = "APP_INTERNAL" in msg_upper or "PY_LOG" in msg_upper

        # 3. Determine "Entropy" (Is this just a random string?)
        has_metadata = len(discovered_tags) > 0

        return {
            **discovered_tags,
            "is_internal": is_internal,
            "parsed_via": "custom_fallback",
            "quality_score": "HIGH" if has_metadata else "LOW"
        }