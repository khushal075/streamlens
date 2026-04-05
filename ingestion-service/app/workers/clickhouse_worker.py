"""
ClickHouse Sink Worker
----------------------
Role: The Consumer.
Logic: Subscribes to the 'structured-logs' Kafka topic, fetches batches, 
       persists them to ClickHouse, and commits offsets only on success.
"""

import asyncio
import logging
import signal
from typing import List, Dict, Any

from app.core.config import settings
from app.messaging.factory import messaging_factory  # Assuming factory handles consumers
from app.storage.factory import storage_client

logger = logging.getLogger(__name__)


class ClickHouseWorker:
    """
    Manages the lifecycle of the Kafka-to-ClickHouse data pipeline.
    """

    def __init__(self):
        self.is_running = True
        self.batch_size = settings.CLICKHOUSE_BATCH_SIZE
        self.consumer = None

    async def start(self):
        """
        Main worker loop. 
        Connects to storage and starts consuming from Kafka.
        """
        # 1. Initialize Storage & Messaging
        storage_client.connect()

        # We need a consumer from the factory
        self.consumer = messaging_factory.get_consumer(
            topic=settings.KAFKA_STRUCTURED_TOPIC,
            group_id="clickhouse-sink-group"
        )
        await self.consumer.start()

        logger.info(f"🚀 ClickHouse Sink Worker started. Group: clickhouse-sink-group")

        try:
            while self.is_running:
                # 2. PULL: Fetch a batch from Kafka
                # We use a timeout to ensure the loop stays alive even if traffic is low
                batch: List[Dict[str, Any]] = await self.consumer.fetch_batch(
                    max_records=self.batch_size,
                    timeout=1.0
                )

                if not batch:
                    continue

                try:
                    # 3. SAVE: Hit ClickHouse with the batch
                    storage_client.insert_logs(batch)

                    # 4. COMMIT: Tell Kafka we safely stored these
                    # This ensures "At-Least-Once" delivery
                    await self.consumer.commit()
                    logger.debug(f"✅ Persisted {len(batch)} logs to ClickHouse.")

                except Exception as e:
                    logger.error(f"❌ ClickHouse Insert Failed: {e}")
                    # BACKOFF: Wait before retrying to avoid spamming a down DB
                    await asyncio.sleep(5)
                    # We do NOT commit here, so the same batch will be retried

        except asyncio.CancelledError:
            logger.info("🛑 Worker task cancelled.")
        finally:
            await self.stop()

    async def stop(self):
        """Graceful shutdown of all connections."""
        self.is_running = False
        if self.consumer:
            await self.consumer.stop()
        storage_client.disconnect()
        logger.info("👋 ClickHouse Worker shutdown complete.")


# --- EXECUTION ---

async def run_worker():
    worker = ClickHouseWorker()

    # Handle OS signals for graceful shutdown (Docker/K8s)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))

    await worker.start()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        pass