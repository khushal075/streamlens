"""
Kafka Ingestion Worker
----------------------
Patterns: Observer, Resource Pool, Template Method, Strategy.
"""

import asyncio
import logging
import signal
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from app.core.config import settings
from app.queue import log_queue  # Standardized from your log_buffer
from app.services.processors.factory import processor_factory
from app.messaging.factory import get_producer

logger = logging.getLogger(__name__)

class KafkaIngestionWorker:
    def __init__(self):
        # PERK 2: Resource Pool (ThreadPool for CPU-bound Regex)
        self.executor = ThreadPoolExecutor(
            max_workers=settings.WORKER_THREADS,
            thread_name_prefix="KafkaWorker"
        )
        self.producer = get_producer()
        self.is_running = False

    def _transform_logs_command(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        PERK: Strategy Pattern.
        Transformation logic executed in the ThreadPool.
        """
        processed_batch = []
        for envelope in batch:
            try:
                # Strategy Selection via Processor Factory
                source = envelope.get("source", "generic")
                processor = processor_factory.get_processor(source)

                # Logic Execution
                structured_data = processor.parse_message(envelope.get("raw_payload", ""))

                # Enrichment
                envelope["attributes"] = structured_data
                processed_batch.append(envelope)
            except Exception as e:
                logger.error(f"❌ Transformation error: {e}")
                continue
        return processed_batch

    async def start(self):
        """
        PERK 1 & 3: Observer Polling + Template Method Workflow.
        """
        self.is_running = True
        logger.info("🚀 KafkaIngestionWorker starting...")

        await log_queue.connect()
        await self.producer.start()
        loop = asyncio.get_running_loop()

        try:
            while self.is_running:
                # 1. FETCH (IO-bound)
                batch = await log_queue.pop_batch(batch_size=settings.BATCH_SIZE)

                if not batch:
                    # Adaptive back-off
                    await asyncio.sleep(settings.WORKER_SLEEP_TIME)
                    continue

                try:
                    # 2. TRANSFORM (CPU-bound - Offloaded to Threads)
                    processed_logs = await loop.run_in_executor(
                        self.executor,
                        self._transform_logs_command,
                        batch
                    )

                    # 3. PUBLISH (IO-bound)
                    if processed_logs:
                        await self.producer.send_batch(processed_logs)
                        logger.debug(f"📤 Flushed {len(processed_logs)} logs to Kafka.")

                except Exception as e:
                    logger.error(f"🔥 Batch processing error: {e}")
                    await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info("🛑 Kafka Worker cancellation received.")
        finally:
            await self.stop()

    async def stop(self):
        """Gracefully shuts down the Kafka connection and ThreadPool."""
        self.is_running = False
        await self.producer.stop()
        await log_queue.disconnect()
        self.executor.shutdown(wait=True) # Ensure threads finish work
        logger.info("👋 Kafka Worker shutdown complete.")

# --- Singleton Runner ---

async def run_worker():
    worker = KafkaIngestionWorker()

    # Handle OS Termination Signals for Docker/K8s
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))

    await worker.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        pass