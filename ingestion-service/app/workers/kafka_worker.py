"""
Kafka Worker Service
--------------------
Role: The 'Bridge' between local buffering (Redis) and distributed messaging (Kafka).

Patterns:
1. Observer (Polling): Continuously monitors the Redis buffer for new data.
2. Resource Pool: Manages a ThreadPool for CPU-heavy Regex/Parsing to keep the Event Loop responsive.
3. Template Method: Defines a standardized 'Fetch -> Transform -> Publish' workflow.
4. Singleton Service: Managed via a global instance for resource sharing.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from app.core.config import settings
from app.services.buffer import log_buffer
from app.services.processors.factory import processor_factory
from app.messaging.factory import get_producer  # Your Kafka Producer Factory

logger = logging.getLogger(__name__)

class KafkaIngestionWorker:
    """
    A high-performance background worker that transforms raw logs
    and publishes them to a Kafka cluster.
    """

    def __init__(self):
        # RESOURCE POOL: Dedicated threads for Regex/String manipulation
        # This prevents CPU-heavy tasks from blocking incoming API requests.
        self.executor = ThreadPoolExecutor(
            max_workers=settings.WORKER_THREADS,
            thread_name_prefix="KafkaWorker"
        )
        self.producer = get_producer()
        self.is_running = False

    def _transform_logs_command(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        INTERNAL COMMAND: The transformation logic executed in the ThreadPool.
        Uses the Strategy Pattern (Processor Factory) to structure raw data.
        """
        processed_batch = []
        for envelope in batch:
            try:
                # 1. Strategy Selection
                source = envelope.get("source", "generic")
                processor = processor_factory.get_processor(source)

                # 2. Logic Execution (Regex / Field Mapping)
                # We extract the 'raw_payload' and turn it into 'attributes'
                structured_data = processor.parse_message(envelope.get("raw_payload", ""))

                # 3. Enrichment
                # Merge the structured data back into the standardized envelope
                envelope["attributes"] = structured_data
                processed_batch.append(envelope)
            except Exception as e:
                logger.error(f"Failed to transform log in worker: {e}")
                continue
        return processed_batch

    async def start(self):
        """
        TEMPLATE METHOD: The skeletal algorithm for the worker loop.
        POLLING OBSERVER: Watches Redis for work.
        """
        self.is_running = True
        logger.info("🚀 KafkaIngestionWorker starting...")

        # Ensure the Kafka Producer is connected
        await self.producer.start()
        loop = asyncio.get_running_loop()

        try:
            while self.is_running:
                # 1. FETCH (IO-bound)
                batch = await log_buffer.dequeue_batch(count=settings.BATCH_SIZE)

                if not batch:
                    # Adaptive back-off to prevent CPU spinning
                    await asyncio.sleep(settings.WORKER_SLEEP_TIME)
                    continue

                try:
                    # 2. TRANSFORM (CPU-bound - Offloaded to ThreadPool)
                    # This keeps the main thread free to handle new incoming logs.
                    processed_logs = await loop.run_in_executor(
                        self.executor,
                        self._transform_logs_command,
                        batch
                    )

                    # 3. PUBLISH (IO-bound)
                    if processed_logs:
                        await self.producer.send_batch(processed_logs)
                        logger.debug(f"Flushed {len(processed_logs)} logs to Kafka.")

                except Exception as e:
                    logger.error(f"🔥 Batch processing error in Kafka Worker: {e}")
                    await asyncio.sleep(1) # Back-off on error

        except asyncio.CancelledError:
            logger.info("🛑 Kafka Worker cancellation received.")
        finally:
            await self.stop()

    async def stop(self):
        """Graceful shutdown of resources."""
        self.is_running = False
        logger.info("Closing Kafka Worker connections...")

        # Close Kafka connection
        await self.producer.stop()

        # Shutdown ThreadPool
        self.executor.shutdown(wait=True)
        logger.info("👋 Kafka Worker shutdown complete.")

# --- GLOBAL INSTANCE ---
# This ensures we don't accidentally create multiple thread pools.
kafka_ingestion_worker = KafkaIngestionWorker()