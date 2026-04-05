"""
ClickHouse Storage Provider
---------------------------
Role: The High-Performance OLAP Sink.
Logic: Uses the MergeTree engine with LowCardinality optimization for
       high-compression and fast analytical queries.
"""

import clickhouse_connect
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.storage.base import BaseStorageClient

logger = logging.getLogger(__name__)

class ClickHouseStorage(BaseStorageClient):
    """
    Concrete implementation of BaseStorageClient for ClickHouse.
    """

    def __init__(self):
        self.client = None

    def connect(self) -> None:
        """Initializes the connection and ensures the schema exists."""
        if not self.client:
            try:
                self.client = clickhouse_connect.get_client(
                    host=settings.CLICKHOUSE_HOST,
                    port=settings.CLICKHOUSE_PORT,
                    username=settings.CLICKHOUSE_USER,
                    password=settings.CLICKHOUSE_PASSWORD,
                    database=settings.CLICKHOUSE_DATABASE
                )
                self._ensure_table()
                logger.info("🏛️ ClickHouse connection established and schema verified.")
            except Exception as e:
                logger.critical(f"❌ Could not connect to ClickHouse: {e}")
                raise

    def disconnect(self) -> None:
        """Gracefully closes the ClickHouse client."""
        if self.client:
            self.client.close()
            logger.info("🏛️ ClickHouse connection closed.")

    def _ensure_table(self):
        """
        Creates the logs table if it doesn't exist.
        Optimization: Uses LowCardinality for repeated strings to save ~80% disk space.
        """
        query = """
        CREATE TABLE IF NOT EXISTS logs (
            timestamp DateTime64(3, 'UTC'),
            tenant_id UInt32,
            service LowCardinality(String),
            level LowCardinality(String),
            message String,
            metadata Map(String, String),
            ingested_at DateTime DEFAULT now()
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(timestamp)
        ORDER BY (tenant_id, service, timestamp);
        """
        self.client.command(query)

    def insert_logs(self, batch: List[Dict[str, Any]]) -> None:
        """
        Persists a batch of logs to ClickHouse.
        Converts the incoming list of dictionaries into a list of tuples
        matching the table schema.
        """
        if not batch or not self.client:
            return

        # Prepare data for bulk insert (Map dict keys to table columns)
        data = [
            (
                log.get("timestamp"),
                log.get("tenant_id"),
                log.get("service", "unknown"),
                log.get("level", "INFO"),
                log.get("message", ""),
                log.get("metadata", {})
            )
            for log in batch
        ]

        try:
            self.client.insert(
                'logs',
                data,
                column_names=[
                    'timestamp', 'tenant_id', 'service',
                    'level', 'message', 'metadata'
                ]
            )
            logger.debug(f"Successfully flushed {len(batch)} logs to ClickHouse")
        except Exception as e:
            logger.error(f"❌ ClickHouse Insert Error: {e}")
            raise