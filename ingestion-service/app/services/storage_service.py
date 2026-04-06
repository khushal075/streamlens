"""
Storage Service
---------------
Role: The 'Librarian' of the ingestion pipeline.

Purpose:
1. Schema Mapping: Converts flexible Processor dictionaries into strict ClickHouse tuples.
2. Batch Execution: Directs the ClickHouseClient to perform high-speed insertions.
3. Decoupling: Provides a clean interface for the Kafka Worker to save data.
"""

import logging
from typing import List, Dict, Any, Tuple
from app.storage.clickhouse import ClickHouseStorage

logger = logging.getLogger(__name__)


class StorageService:
    """
    Orchestrates the movement of processed log data into permanent storage.

    This service acts as a bridge between the 'Logic' (Processors)
    and the 'Physical Storage' (ClickHouse/S3).
    """

    def __init__(self):
        # Initialize the low-level database client
        self.clickhouse_client = ClickHouseStorage()

    def _prepare_for_clickhouse(self, processed_logs: List[Dict[str, Any]]) -> List[Tuple]:
        """
        Converts the dictionary output from processors into
        the tuple format expected by the ClickHouse table schema.

        Schema Order: (timestamp, tenant_id, service, source, level, message, metadata)
        """
        batch = []
        for log in processed_logs:
            try:
                # We extract the keys that our Processors and Grandfather (BaseLogProcessor)
                # have painstakingly cleaned and normalized.
                tuple_row = (
                    log.get('timestamp'),
                    log.get('tenant_id', 0),
                    log.get('service', 'default'),
                    log.get('source', 'generic'),
                    log.get('level', 'INFO'),
                    log.get('message', ''),
                    # 'metadata' here maps to the 'attributes' or 'extra' fields from processors
                    log.get('metadata', {})
                )
                batch.append(tuple_row)
            except Exception as e:
                logger.error(f"Error formatting log for ClickHouse: {e}")
                continue
        return batch

    async def save_logs(self, processed_logs: List[Dict[str, Any]]):
        """
        High-level method called by the Kafka Worker to persist a batch.

        Args:
            processed_logs (List[Dict]): Cleaned logs from the Processor Tree.
        """
        if not processed_logs:
            return

        # 1. Transform dicts to strict tuples for the SQL driver
        batch = self._prepare_for_clickhouse(processed_logs)

        # 2. Insert into ClickHouse using the low-level client
        if batch:
            try:
                # Assuming ClickHouseClient.insert_batch is or can be made async
                await self.clickhouse_client.insert_batch(batch)
                logger.info(f"Successfully stored batch of {len(batch)} logs.")
            except Exception as e:
                logger.error(f"Failed to persist batch to ClickHouse: {e}")
                # This is where you would implement a 'Retry' or 'Dead Letter' logic
                raise


# --- GLOBAL INSTANCE ---
storage_service = StorageService()