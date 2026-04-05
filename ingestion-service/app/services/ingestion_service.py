"""
Ingestion Service
-----------------
Role: The 'Receptionist' of the pipeline.

Purpose:
1. Batch Transformation: Efficiently wraps a list of logs into standardized envelopes.
2. Metadata Enrichment: Injects tenant_id, service, and origin_ip for downstream tracking.
3. High-Speed Handoff: Pushes the entire batch to the Redis Buffer (log_buffer) in one operation.
"""

import time
import uuid
import logging
from typing import List, Any
from app.services.buffer import log_buffer

logger = logging.getLogger(__name__)

class IngestionService:
    """
    Coordinates the initial reception and buffering of log data batches.
    """

    async def ingest_batch(
        self,
        logs: List[Any],
        tenant_id: int,
        service: str,
        client_ip: str
    ) -> str:
        """
        The core batch ingestion logic. Standardizes multiple logs and moves
        them to the buffer in a single atomic operation.

        Args:
            logs: List of log objects (Pydantic models from the LogRequest).
            tenant_id: The ID of the organization sending the logs.
            service: The name of the service originating the logs.
            client_ip: The source IP address for audit and security.

        Returns:
            str: A unique ingestion_id generated for this specific batch request.
        """
        # 1. Create a unique ID for the entire batch 'event'
        # This allows us to track all logs that arrived in this single HTTP call.
        ingestion_id = str(uuid.uuid4())

        try:
            # 2. Batch Enveloping
            # Using list comprehension for C-speed performance in Python.
            # We map the incoming Pydantic fields to our internal 'Envelope' structure.
            payload_batch = [
                {
                    "ingestion_id": ingestion_id,
                    "tenant_id": tenant_id,
                    "service": service,
                    "origin_ip": client_ip,
                    "ingest_timestamp": time.time(),
                    # 'message' from Pydantic becomes 'raw_payload' for the Processors
                    "raw_payload": getattr(log, 'message', ""),
                    "metadata": getattr(log, 'metadata', {}) or {},
                    "source": getattr(log, 'source', 'generic').lower()
                }
                for log in logs
            ]

            # 3. Atomic Push to Redis Buffer
            # We use push_batch to perform a single RPUSH to Redis,
            # which is significantly faster than multiple individual pushes.
            await log_buffer.push_batch(payload_batch)

            logger.info(f"Buffered batch {ingestion_id} with {len(payload_batch)} logs for tenant {tenant_id}")
            return ingestion_id

        except Exception as e:
            logger.error(f"Failed to buffer batch {ingestion_id} for tenant {tenant_id}: {e}")
            # Raising allows the API Router to catch the error and return a 500 status.
            raise

    async def ingest(self, log_entry: Any, client_ip: str, tenant_id: int = 0) -> str:
        """
        Legacy/Single log helper. Redirects to ingest_batch for consistency.
        """
        return await self.ingest_batch(
            logs=[log_entry],
            tenant_id=tenant_id,
            service=getattr(log_entry, 'service', 'default'),
            client_ip=client_ip
        )

# --- GLOBAL INSTANCE ---
ingestion_service = IngestionService()