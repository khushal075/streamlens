from fastapi import APIRouter, HTTPException
import asyncio

from app.models.log_model import LogRequest
from app.queue.redis_queue import enqueue, queue_size
from app.services.rate_limiter import is_allowed

router = APIRouter()

MAX_QUEUE_THRESHOLD = 9000
MAX_CONCURRENT_ENQUEUE = 100  # 🔥 control concurrency

# 🔥 Semaphore to limit parallel Redis calls
semaphore = asyncio.Semaphore(MAX_CONCURRENT_ENQUEUE)


async def safe_enqueue(payload: dict):
    async with semaphore:
        await enqueue(payload)


@router.post("/logs")
async def ingest_logs(request: LogRequest):
    # ✅ Rate limiting
    if not is_allowed(request.tenant_id, len(request.logs)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # ✅ Backpressure check (async)
    current_queue_size = await queue_size()
    if current_queue_size > MAX_QUEUE_THRESHOLD:
        raise HTTPException(status_code=503, detail="System overloaded")

    # 🔥 Controlled parallel enqueue
    await asyncio.gather(*[
        safe_enqueue({
            "tenant_id": request.tenant_id,
            "service": request.service,
            **log.dict()
        })
        for log in request.logs
    ])

    return {
        "status": "accepted",
        "count": len(request.logs),
        "queue_size": current_queue_size
    }