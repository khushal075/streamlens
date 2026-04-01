import asyncio
from app.core.config import settings

queue = asyncio.Queue(maxsize=settings.MAX_QUEUE_SIZE)

async def enqueue(item):
    await queue.put(item)

async def dequeue_batch(batch_size):
    items = []
    for _ in range(batch_size):
        if queue.empty():
            break
        items.append(await queue.get())
    return items

def queue_size():
    return queue.qsize()