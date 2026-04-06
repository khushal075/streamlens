import re
import logging
from typing import Dict, Any
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)


class DatabaseProcessor(BaseLogProcessor):
    """
    Handles Logs from MySQL, PostgreSQL, and MongoDB.
    Category: Database Logs (Focus on Slow Queries & Audit)
    """

    # Matches: Query_time: 2.123456  Lock_time: 0.000123  Rows_sent: 5
    SLOW_QUERY_PATTERN = re.compile(
        r'Query_time:\s+(?P<duration>\d+\.\d+).*?Lock_time:\s+(?P<lock_time>\d+\.\d+)'
    )

    # Matches: SELECT * FROM users or UPDATE accounts SET...
    DB_OP_PATTERN = re.compile(r'(?P<operation>SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\s+', re.IGNORECASE)

    def process(self, raw_data: str) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_db_log")

        try:
            metadata = {"parser": "database_v1"}

            # 1. Check for Slow Query Metrics
            slow_match = self.SLOW_QUERY_PATTERN.search(raw_data)
            if slow_match:
                metrics = slow_match.groupdict()
                metadata.update({
                    "query_duration_sec": float(metrics['duration']),
                    "lock_time_sec": float(metrics['lock_time']),
                    "is_slow_query": float(metrics['duration']) > 1.0  # Threshold
                })

            # 2. Extract Database Operation
            op_match = self.DB_OP_PATTERN.search(raw_data)
            if op_match:
                metadata["db_operation"] = op_match.group("operation").upper()

            # 3. Determine Level
            level = "INFO"
            if "error" in raw_data.lower() or "fatal" in raw_data.lower():
                level = "ERROR"
            elif metadata.get("is_slow_query"):
                level = "WARNING"

            return {
                "timestamp": self.get_utc_now(),
                "level": level,
                "message": raw_data[:500],  # Truncate long queries for the message summary
                "metadata": metadata
            }

        except Exception as e:
            logger.error(f"DatabaseProcessor Error: {e}")
            return self._create_fallback(raw_data, "db_parse_exception")