import re
from typing import Dict, Any
from ..base import BaseLogProcessor


class StorageBase(BaseLogProcessor):
    """
    Parent: Logic for Relational (SQL) and NoSQL databases.
    Focuses on Query profiling and Latency.
    """
    # Regex to catch SQL actions and execution times (e.g., "took 45.2ms")
    ACTION_PATTERN = re.compile(r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|FIND|AGGREGATE)\b', re.IGNORECASE)
    LATENCY_PATTERN = re.compile(r'(\d+\.?\d*)\s*(ms|s|µs)')

    def extract_storage_metrics(self, message: str) -> Dict[str, Any]:
        """
        Utility: Scans the log for database-specific metrics.
        """
        action_match = self.ACTION_PATTERN.search(message)
        latency_match = self.LATENCY_PATTERN.search(message)

        metrics = {
            "operation": action_match.group(1).upper() if action_match else "UNKNOWN",
            "duration": 0.0,
            "unit": "ms"
        }

        if latency_match:
            metrics["duration"] = float(latency_match.group(1))
            metrics["unit"] = latency_match.group(2)

        return metrics