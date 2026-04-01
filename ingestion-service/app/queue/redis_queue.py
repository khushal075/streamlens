# app/queue/redis_queue.py

import json
import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)


async def enqueue(item: dict):
    await redis_client.rpush(
        settings.REDIS_QUEUE_NAME,
        json.dumps(item)
    )


async def dequeue_batch(batch_size: int):
    items = []

    for _ in range(batch_size):
        data = await redis_client.lpop(settings.REDIS_QUEUE_NAME)
        if not data:
            break
        items.append(json.loads(data))

    return items


async def queue_size():
    return await redis_client.llen(settings.REDIS_QUEUE_NAME)