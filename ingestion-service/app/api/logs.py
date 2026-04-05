"""
Log Ingestion Router
--------------------
Role: The 'Front Desk' of the API.
Patterns:
- Facade: Delegates all logic to the IngestionService.
- Guardian: Handles HTTP-level exceptions and status codes.
"""

import logging
from fastapi import APIRouter, HTTPException, Request

from app.models.log_model import LogRequest
from app.services.ingestion_service import ingestion_service
from app.services.rate_limiter import rate_limiter
from app.services.buffer import log_buffer

logger = logging.getLogger(__name__)
router = APIRouter()

# Thresholds for backpressure (Could also be moved to settings)
MAX_QUEUE_THRESHOLD = 9000

@router.post("/logs")
async def ingest_logs(request: LogRequest, http_request: Request):
    """
    Primary endpoint for log ingestion.
    Supports batch ingestion with multi-tenant rate limiting and backpressure.
    """
    tenant_id = request.tenant_id
    log_count = len(request.logs)
    client_ip = http_request.client.host

    # 1. PROXY CHECK: Rate Limiting (Distributed Redis)
    # We check before doing any heavy object allocation
    if not await rate_limiter.is_allowed(str(tenant_id), log_count):
        logger.warning(f"Rate limit hit for tenant: {tenant_id}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please slow down."
        )

    # 2. BACKPRESSURE: Check Buffer Health
    current_size = await log_buffer.get_buffer_size()
    if current_size > MAX_QUEUE_THRESHOLD:
        logger.error(f"Backpressure triggered. Buffer size: {current_size}")
        raise HTTPException(
            status_code=503,
            detail="System is currently overloaded. Retry in 30 seconds."
        )

    # 3. FACADE CALL: Delegate to Ingestion Service
    # The service handles enveloping, UUID generation, and pushing to Redis.
    try:
        # We pass the full request to the service to keep the router 'thin'
        ingestion_id = await ingestion_service.ingest_batch(
            logs=request.logs,
            tenant_id=tenant_id,
            service=request.service,
            client_ip=client_ip
        )
    except Exception as e:
        logger.error(f"Ingestion failed for tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error: Failed to buffer logs."
        )

    # 4. RESPONSE
    return {
        "status": "accepted",
        "ingestion_id": ingestion_id,
        "count": log_count,
        "metrics": {
            "buffer_depth": current_size + log_count
        }
    }