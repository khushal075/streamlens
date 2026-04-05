"""
Log Buffering Service
---------------------
Role: The 'Asynchronous Shock Absorber' of the ingestion pipeline.
"""

import json
import logging
from typing import List, Dict, Any, Optional
import aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class LogBuffer:
    """
    Redis-backed buffering system for high-throughput log ingestion.

    This class provides thread-safe (atomic) operations to push single logs
    and pull batches. It acts as a circuit breaker between the synchronous
    API layer and the asynchronous processing workers.
    """

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.BUFFER_KEY = "ingestion:buffer:queue"

    async def connect(self):
        """Lazy-load the Redis connection to ensure it's created within the async loop."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def push(self, log_data: Dict[str, Any]):
        """Serializes and appends a log to the head of the Redis list."""
        try:
            await self.connect()
            await self.redis.lpush(self.BUFFER_KEY, json.dumps(log_data))
        except Exception as e:
            logger.error(f"Buffer push failed: {e}")
            raise

    async def dequeue_batch(self, count: int = 1000) -> List[Dict[str, Any]]:
        """Pops a specified number of logs from the tail of the Redis list atomically."""
        await self.connect()
        async with self.redis.pipeline(transaction=True) as pipe:
            for _ in range(count):
                pipe.rpop(self.BUFFER_KEY)
            results = await pipe.execute()

        return [json.loads(msg) for msg in results if msg]

    async def get_buffer_size(self) -> int:
        """Monitoring: How many logs are currently waiting in Redis?"""
        await self.connect()
        return await self.redis.llen(self.BUFFER_KEY)


# --- GLOBAL INSTANCE ---
# This ensures a single connection pool is shared across the entire app.
log_buffer = LogBuffer()