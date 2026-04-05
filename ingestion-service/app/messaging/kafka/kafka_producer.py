"""
Kafka Producer Implementation
-----------------------------
Role: Concrete implementation of the BaseProducer using AIOKafka.
Strategy: High-throughput async batching with Snappy compression
          and Tenant-aware partitioning.
"""

import orjson
import asyncio
import logging
from typing import List, Dict, Any, Optional

from aiokafka import AIOKafkaProducer
from app.messaging.base.producer import BaseProducer
from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaProducer(BaseProducer):
    """
    Asynchronous Kafka Producer optimized for high-volume log ingestion.

    This implementation uses snappy compression and a small 'linger' time
    to maximize network efficiency. It implements tenant-based partitioning
    to ensure that logs from the same source maintain their chronological order
    within Kafka.
    """

    def __init__(self):
        """Initializes the KafkaProducer instance."""
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        """
        Initializes the AIOKafkaProducer with production-grade settings.

        - acks=all: Maximum durability.
        - snappy: Fast compression balanced with CPU usage.
        - linger_ms=5: Groups small sends into larger packets.
        """
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                acks="all",
                compression_type="snappy",
                linger_ms=5,
                max_batch_size=65536,
            )
            await self.producer.start()
            logger.info("✅ Kafka producer started successfully")

    async def stop(self) -> None:
        """Gracefully shuts down the producer and flushes internal buffers."""
        if self.producer:
            await self.producer.stop()
            logger.info("🛑 Kafka producer stopped")

    async def send_batch(self, messages: List[Dict[str, Any]]) -> None:
        """
        Sends a batch of logs to Kafka in parallel.

        Args:
            messages (List[Dict[str, Any]]): Processed log envelopes to publish.
        """
        if not self.producer:
            logger.error("Producer not started")
            raise RuntimeError("Producer not started")

        if not messages:
            return

        tasks = []
        for msg in messages:
            try:
                # 1. Handle Partitioning (Tenant-based routing for ordering)
                key = self._get_partition_key(msg)

                # 2. Serialize using orjson (Directly to bytes)
                binary_data = orjson.dumps(
                    msg,
                    option=orjson.OPT_UTC_Z
                )

                # 3. Create the send task
                task = self.producer.send(
                    topic=settings.KAFKA_TOPIC,
                    key=key,
                    value=binary_data
                )
                tasks.append(task)

            except Exception as e:
                logger.error(f"❌ Serialization error for message: {e}")
                continue

        # 4. 🔥 Execute all sends in parallel for the batch
        if tasks:
            try:
                await asyncio.gather(*tasks)
                logger.debug(f"Successfully buffered {len(tasks)} messages to Kafka")
            except Exception as e:
                logger.error(f"🔥 Error during batch send: {e}")
                raise

    def _get_partition_key(self, msg: Dict[str, Any]) -> bytes:
        """
        Generates a key to ensure logs from the same tenant/service land
        in the same Kafka partition.
        """
        tenant = msg.get("tenant_id", "unknown")
        service = msg.get("service", "unknown")
        return f"{tenant}:{service}".encode("utf-8")