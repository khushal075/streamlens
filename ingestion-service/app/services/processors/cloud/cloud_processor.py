from .base import CloudBase
from typing import Dict, Any


class CloudProcessor(CloudBase):
    """
    Child: Specific logic for AWS, GCP, and Azure.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Extract the high-level cloud context
        cloud_meta = self.extract_cloud_context(raw_message)

        # 2. Logic: Detect Service Type
        msg_upper = str(raw_message).upper()
        service_type = "COMPUTE"  # Default

        if "LAMBDA" in msg_upper or "FUNCTION" in msg_upper:
            service_type = "SERVERLESS"
        elif "S3" in msg_upper or "BLOB" in msg_upper:
            service_type = "STORAGE"
        elif "VPC" in msg_upper or "SUBNET" in msg_upper:
            service_type = "NETWORKING"

        return {
            **cloud_meta,
            "cloud_service": service_type,
            "is_production": cloud_meta["region"] not in ["us-east-1-test", "dev-region"]
        }