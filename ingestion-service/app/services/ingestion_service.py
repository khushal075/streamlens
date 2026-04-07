import logging
from typing import List, Any

# --- NEW COMMON IMPORTS ---
from streamlens_common.models import LogEnvelope        # The shared Data Contract
from streamlens_common.utils.helpers import (           # Standardized helpers
    generate_event_id,
    get_current_utc
)
from streamlens_common.logging.logger import get_logger

# --- SERVICE IMPORTS ---
from app.services.buffer import log_buffer

# Standardized logger from common
logger = get_logger(__name__)

class IngestionService:
    """
    Coordinates the initial reception and buffering of log data batches.
    Refactored to use the 'streamlens_common' shared library.
    """

    async def ingest_batch(
        self,
        logs: List[Any],
        tenant_id: str, # Changed to str to match LogEnvelope standard
        service: str,
        client_ip: str
    ) -> str:
        """
        Transforms raw logs into standardized LogEnvelopes and pushes to Redis.
        """
        # 1. Use common utility for batch/ingestion tracking
        ingestion_id = generate_event_id()

        try:
            # 2. Batch Enveloping
            # We map raw logs into the formal LogEnvelope Pydantic model.
            # This ensures that every log in the buffer is 100% valid.
            payload_batch = [
                LogEnvelope(
                    event_id=generate_event_id(),
                    ingestion_id=ingestion_id,
                    tenant_id=str(tenant_id),
                    service_name=service,
                    origin_ip=client_ip,
                    timestamp=get_current_utc(),
                    # Extracting data from the raw input
                    raw_payload=log.get("message", "") if isinstance(log, dict) else getattr(log, 'message', ""),
                    metadata=log.get("metadata", {}) if isinstance(log, dict) else getattr(log, 'metadata', {}),
                    source=log.get("source", "generic").lower() if isinstance(log, dict) else getattr(log, 'source', 'generic').lower()
                ).model_dump() # Convert to dict for Redis storage
                for log in logs
            ]

            # 3. Atomic Push to Redis Buffer
            await log_buffer.push_batch(payload_batch)

            logger.info(f"Buffered batch {ingestion_id} | Logs: {len(payload_batch)} | Tenant: {tenant_id}")
            return ingestion_id

        except Exception as e:
            logger.error(f"Failed to buffer batch {ingestion_id}: {e}")
            raise

    async def ingest(self, log_entry: Any, client_ip: str, tenant_id: str = "0") -> str:
        """
        Legacy/Single log helper. Redirects to ingest_batch for consistency.
        """
        # Extract service name safely
        service_name = log_entry.get("service", "default") if isinstance(log_entry, dict) else getattr(log_entry, 'service', 'default')

        return await self.ingest_batch(
            logs=[log_entry],
            tenant_id=tenant_id,
            service=service_name,
            client_ip=client_ip
        )

# --- GLOBAL INSTANCE ---
ingestion_service = IngestionService()