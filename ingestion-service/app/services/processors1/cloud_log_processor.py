import orjson
import logging
from typing import Dict, Any, Union
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)


class CloudLogProcessor(BaseLogProcessor):
    """
    Handles Cloud Platform Logs (AWS, GCP, Azure).
    Focuses on flattening nested JSON structures for ClickHouse indexing.
    """

    def process(self, raw_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        # 1. New Base Utility: Validation
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_cloud_payload")

        try:
            # 2. Performance: Use orjson for faster parsing
            data = raw_data
            if isinstance(raw_data, (str, bytes)):
                data = orjson.loads(raw_data)

            # 3. Standardized Cloud Extraction
            return {
                "timestamp": data.get("eventTime") or data.get("timestamp") or self.get_utc_now(),
                "level": self._determine_level(data),
                # Method/Event name is the 'action' in cloud logs
                "message": (
                        data.get("eventName") or
                        data.get("protoPayload", {}).get("methodName") or
                        "Cloud Infrastructure Event"
                ),
                "metadata": self._flatten_metadata(data)
            }

        except Exception as e:
            logger.error(f"Cloud Logic Error: {e}")
            # 4. New Base Utility: Standardized Fallback
            return self._create_fallback(raw_data, "cloud_json_parse_fail")

    def _determine_level(self, data: Dict[str, Any]) -> str:
        """Heuristic to detect errors in Cloud Provider schemas."""
        # AWS uses errorCode, GCP often uses status codes/severity
        has_error = (
                data.get("errorCode") or
                data.get("errorMessage") or
                data.get("severity") in ["ERROR", "CRITICAL", "ALERT"]
        )
        return "ERROR" if has_error else "INFO"

    def _flatten_metadata(self, data: Dict[str, Any]) -> Dict[str, str]:
        """
        Extracts key cloud identifiers into a flat structure.
        ClickHouse performs best when high-cardinality fields are at the top level.
        """
        # Map disparate cloud provider fields to common internal keys
        flat = {
            "cloud_region": str(data.get("awsRegion") or data.get("location") or ""),
            "source_ip": str(data.get("sourceIPAddress") or data.get("requestMetadata", {}).get("callerIp") or ""),
            "user_agent": str(data.get("userAgent") or ""),
            "account_id": str(
                data.get("recipientAccountId") or data.get("resource", {}).get("labels", {}).get("project_id") or ""),
            "event_source": str(data.get("eventSource") or ""),
            "parser": "cloud_v1"
        }
        # Clean up empty strings to save storage space
        return {k: v for k, v in flat.items() if v}