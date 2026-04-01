# app/messaging/kafka/kafka_producer.py

import json
from typing import List, Dict, Any

from aiokafka import AIOKafkaProducer

from app.messaging.base.producer import BaseProducer
from app.core.config import settings


class KafkaProducer(BaseProducer):

    def __init__(self):
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,

            # ✅ Reliability
            acks="all",

            # ✅ Performance
            compression_type="snappy",
            linger_ms=5,
            max_batch_size=65536,
        )

        await self.producer.start()
        print("✅ Kafka producer started")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            print("🛑 Kafka producer stopped")

    async def send_batch(self, messages: List[Dict[str, Any]]):
        if not self.producer:
            raise RuntimeError("Producer not started")

        for msg in messages:
            key = self._get_partition_key(msg)

            self.producer.send(
                topic=settings.KAFKA_TOPIC,
                key=key,
                value=json.dumps(msg).encode("utf-8")
            )

    def _get_partition_key(self, msg: Dict[str, Any]) -> bytes:
        tenant = msg.get("tenant_id", "unknown")
        service = msg.get("service", "unknown")

        return f"{tenant}:{service}".encode("utf-8")