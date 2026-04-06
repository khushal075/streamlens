"""
Rate Limiter Service
--------------------
Role: The 'Bouncer' of the ingestion pipeline.

Purpose:
1. Distributed Limiting: Syncs limits across all API worker instances using Redis.
2. Tenant Protection: Prevents one tenant from exhausting system resources.
3. Burst Management: Uses a 1-second window to match your current logic.
"""

import time
import logging
from typing import Optional
from redis import asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Redis-based rate limiting. 
    Replaces in-memory defaultdict to support distributed API scaling.
    """

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        # Matching your current business logic:
        self.RATE_LIMIT = 1000  # logs per second
        self.WINDOW_SIZE = 1  # 1 second window

    async def connect(self):
        """Lazy-load the Redis connection."""
        if not self.redis:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

    async def is_allowed(self, tenant_id: str, logs_count: int) -> bool:
        """
        Determines if a tenant is allowed to ingest a batch of logs.

        Args:
            tenant_id (str): Unique identifier for the tenant.
            logs_count (int): Number of logs in the current request.
        """
        await self.connect()

        # Create a key unique to the current second
        # Format: ratelimit:tenant_123:1712345678
        now = int(time.time())
        key = f"ratelimit:{tenant_id}:{now}"

        try:
            # Use a Redis Pipeline for atomicity and speed
            async with self.redis.pipeline(transaction=True) as pipe:
                # 1. Add the current batch count to the total for this second
                pipe.incrby(key, logs_count)
                # 2. Set expiry so Redis cleans up automatically after the second passes
                pipe.expire(key, self.WINDOW_SIZE + 2)
                results = await pipe.execute()

            current_total = results[0]

            if current_total > self.RATE_LIMIT:
                logger.warning(f"Rate limit exceeded for {tenant_id}: {current_total}/{self.RATE_LIMIT}")
                return False

            return True

        except Exception as e:
            logger.error(f"Rate limiter failure: {e}. Failing open to prioritize availability.")
            return True


# --- GLOBAL INSTANCE ---
rate_limiter = RateLimiter()