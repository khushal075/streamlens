import asyncio
import logging
from app.core.config import settings
from app.messaging.factory import get_consumer  # You'll need a consumer factory
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


async def clickhouse_worker():
    """
    The 'Final Destination' Worker:
    Kafka (Structured) -> StorageService -> ClickHouse
    """
    # 1. Initialize our high-level storage coordinator
    storage_service = StorageService()

    # 2. Get the Consumer (Ensure your factory can return a Kafka consumer)
    consumer = get_consumer(
        topic=settings.KAFKA_STRUCTURED_TOPIC,
        group_id="clickhouse-sink-group"
    )

    logger.info("🏗️ Starting StreamLens ClickHouse Sink Worker...")
    await consumer.start()

    try:
        while True:
            # 3. PULL: Get a batch of already-structured logs from Kafka
            batch = await consumer.fetch_batch(
                max_records=settings.BATCH_SIZE,
                timeout=1.0
            )

            if not batch:
                await asyncio.sleep(settings.WORKER_SLEEP_TIME)
                continue

            try:
                # 4. SAVE: The StorageService handles the Dict -> Tuple conversion
                # and hits the ClickHouseClient.insert_batch()
                storage_service.save_logs(batch)

                # 5. COMMIT: Tell Kafka we safely stored these in the DB
                await consumer.commit()

            except Exception as e:
                logger.error(f"❌ ClickHouse Save Failed: {e}")
                # We back off and DO NOT commit, so we can retry this batch
                await asyncio.sleep(2)

    except asyncio.CancelledError:
        logger.info("🛑 ClickHouse Worker stopping...")
    finally:
        await consumer.stop()
        logger.info("👋 Sink Worker shutdown complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(clickhouse_worker())