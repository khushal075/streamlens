import json
from typing import Dict, Any
from ..base import BaseLogProcessor


class CloudBase(BaseLogProcessor):
    """
    Parent: Handles Cloud Metadata (AWS, GCP, Azure).
    Focuses on Regions, Account IDs, and Resource ARNs.
    """

    def extract_cloud_context(self, raw_message: str) -> Dict[str, Any]:
        """
        Utility: Attempts to find common cloud metadata keys.
        """
        try:
            # Most cloud logs are delivered as JSON strings
            data = json.loads(raw_message) if isinstance(raw_message, str) else raw_message

            return {
                "provider": data.get("provider") or data.get("cloud_provider", "unknown"),
                "region": data.get("region") or data.get("aws_region", "global"),
                "account_id": data.get("account_id") or data.get("owner", "internal"),
                "resource_id": data.get("resource_id") or data.get("arn", "unassigned")
            }
        except (json.JSONDecodeError, AttributeError):
            return {
                "provider": "unknown",
                "region": "global",
                "account_id": "none",
                "resource_id": "raw_stream"
            }