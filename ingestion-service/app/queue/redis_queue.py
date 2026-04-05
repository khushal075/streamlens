"""
Redis Queue Service
-------------------
Role: The High-Performance Persistent Buffer.
Pattern: Provider / Singleton.
Logic: Uses Atomic Pipelines (LRANGE + LTRIM) to ensure that log batches
       are retrieved and removed as a single unit of work.
"""

import json
import logging
import redis.asyncio as redis
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisQueue:
    """
    Manages the connection and operations for the Redis-backed log buffer.

    This service provides an asynchronous interface to interact with a Redis List
    acting as a FIFO queue. It utilizes connection pooling for concurrency and
    atomic pipelines to ensure data integrity during worker consumption.

    Attributes:
        client (Optional[redis.Redis]): The underlying Redis client instance.
        queue_name (str): The Redis key used to store the log queue.
    """

    def __init__(self):
        """Initializes the RedisQueue instance with configuration settings."""
        self.client: Optional[redis.Redis] = None
        self.queue_name = settings.REDIS_QUEUE_NAME

    async def connect(self):
        """
        Initializes the Redis client with a managed connection pool.

        This should be called during the FastAPI startup lifespan to ensure
        the connection is warm before the first request arrives.
        """
        if not self.client:
            try:
                self.client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    decode_responses=True,
                    max_connections=settings.MAX_REDIS_CONNECTIONS
                )
                # Verify connection health
                await self.client.ping()
                logger.info(f"🔌 Connected to Redis Queue at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                logger.error(f"❌ Failed to connect to Redis: {e}")
                raise

    async def disconnect(self):
        """
        Gracefully closes the Redis connection pool.

        This should be called during the FastAPI shutdown lifespan to prevent
        hanging sockets or leaked connections.
        """
        if self.client:
            await self.client.close()
            logger.info("🔌 Redis connection closed.")

    async def push_batch(self, items: List[Dict[str, Any]]):
        """
        ATOMIC PUSH: Pushes multiple items to the tail of the list in one RTT.

        Args:
            items (List[Dict[str, Any]]): A list of standardized log envelopes to buffer.
        """
        if not items or not self.client:
            return

        try:
            # Serialize dictionaries to JSON strings
            serialized_items = [json.dumps(item) for item in items]

            # Variadic RPUSH: RPUSH key val1 val2 val3...
            await self.client.rpush(self.queue_name, *serialized_items)

            # Optional: Enforce a hard cap on the queue size (Backpressure backup)
            # await self.client.ltrim(self.queue_name, -settings.MAX_QUEUE_SIZE, -1)

        except Exception as e:
            logger.error(f"Redis Push Error: {e}")
            raise

    async def pop_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """
        ATOMIC POP: Fetches and removes a block of logs using a Redis Pipeline.

        This ensures that once a worker retrieves a batch, it is immediately
        removed from the list so no other worker instance can process the same data.

        Args:
            batch_size (int): The maximum number of logs to retrieve in this batch.

        Returns:
            List[Dict[str, Any]]: A list of deserialized log dictionaries.
        """
        if not self.client:
            return []

        try:
            async with self.client.pipeline(transaction=True) as pipe:
                # 1. Fetch the range (0 to N-1)
                pipe.lrange(self.queue_name, 0, batch_size - 1)
                # 2. Trim the list (Removes the fetched range)
                pipe.ltrim(self.queue_name, batch_size, -1)

                # Execute the multi-command transaction
                results = await pipe.execute()

            raw_data_list = results[0]

            if not raw_data_list:
                return []

            # Deserialize JSON strings back into Python dictionaries
            return [json.loads(data) for data in raw_data_list]

        except Exception as e:
            logger.error(f"Redis Pop Error: {e}")
            return []

    async def queue_size(self) -> int:
        """
        Returns the current number of logs waiting in the buffer.

        Returns:
            int: The current length of the Redis list.
        """
        if not self.client:
            return 0
        return await self.client.llen(self.queue_name)


# --- GLOBAL INSTANCE ---
# This instance is imported and used by the Ingestion Service and Workers.
log_queue = RedisQueue()