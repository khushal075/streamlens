# app/workers/kafka_worker.py

import asyncio
from app.queue.in_memory_queue import dequeue_batch
from app.core.config import settings
from app.messaging.factory import get_producer

producer = get_producer()


async def kafka_worker():
    await producer.start()

    while True:
        batch = await dequeue_batch(settings.BATCH_SIZE)

        if not batch:
            await asyncio.sleep(0.05)
            continue

        try:
            await producer.send_batch(batch)

        except Exception as e:
            print(f"Batch failed: {e}")
            await asyncio.sleep(1)