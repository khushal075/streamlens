import logging
from typing import List
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

# --- NEW COMMON IMPORTS ---
from streamlens_common.models import LogEnvelope        # The shared data contract
from streamlens_common.logging.logger import get_logger # Standardized logging
from app.core.config import settings                    # Updated to inherit from GlobalSettings

# --- SERVICE IMPORTS ---
from app.services.ingestion_service import ingestion_service
from app.services.rate_limiter import rate_limiter
from app.services.buffer import log_buffer

# Use the standardized logger
logger = get_logger(__name__)
router = APIRouter()

# 1. Update the Request Model to use the Common Envelope
# If your API accepts a list of raw logs, we wrap them here.
class IngestionRequest(BaseModel):
    tenant_id: str
    service: str
    logs: List[dict] # Raw logs before they are "enveloped" by the service

@router.post("/logs", status_code=status.HTTP_202_ACCEPTED)
async def ingest_logs(request: IngestionRequest, http_request: Request):
    """
    Primary endpoint for log ingestion.
    Refactored to use streamlens_common.
    """
    tenant_id = request.tenant_id
    log_count = len(request.logs)
    client_ip = http_request.client.host

    # 1. PROXY CHECK: Rate Limiting
    if not await rate_limiter.is_allowed(tenant_id, log_count):
        logger.warning(f"Rate limit hit for tenant: {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please slow down."
        )

    # 2. BACKPRESSURE: Check Buffer Health (Using settings from common)
    current_size = await log_buffer.get_buffer_size()
    if current_size > settings.MAX_QUEUE_SIZE: # Now defined in config.py
        logger.error(f"Backpressure triggered. Buffer size: {current_size}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is currently overloaded. Retry later."
        )

    # 3. FACADE CALL: Delegate to Ingestion Service
    try:
        # The ingestion_service will now convert these raw dicts
        # into LogEnvelope objects from common.
        ingestion_id = await ingestion_service.ingest_batch(
            logs=request.logs,
            tenant_id=tenant_id,
            service=request.service,
            client_ip=client_ip
        )
    except Exception as e:
        logger.error(f"Ingestion failed for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error: Failed to buffer logs."
        )

    return {
        "status": "accepted",
        "ingestion_id": ingestion_id,
        "count": log_count,
        "metrics": {
            "buffer_depth": current_size + log_count
        }
    }