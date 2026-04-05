from .base import StorageBase
from typing import Dict, Any


class DatabaseProcessor(StorageBase):
    """
    Child: Specific logic for MySQL, PostgreSQL, and MongoDB.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Get shared DB metrics from Parent
        metrics = self.extract_storage_metrics(raw_message)

        # 2. Logic: Determine if it's a slow query based on a 100ms threshold
        is_slow = False
        if metrics["unit"] == "ms" and metrics["duration"] > 100.0:
            is_slow = True
        elif metrics["unit"] == "s" and metrics["duration"] > 0.1:
            is_slow = True

        return {
            **metrics,
            "is_slow_query": is_slow,
            "db_family": "rdbms" if any(x in raw_message.lower() for x in ["mysql", "postgres"]) else "nosql"
        }