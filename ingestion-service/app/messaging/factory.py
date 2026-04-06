"""
Messaging Factory
-----------------
Role: Singleton provider for Producers and Factory for Consumers.
Pattern: Factory / Singleton.
"""

import logging
from typing import Optional
from app.core.config import settings
from app.messaging.base.producer import BaseProducer
from app.messaging.kafka.kafka_producer import KafkaProducer
from app.messaging.kafka.kafka_consumer import KafkaConsumer  # 👈 New Import

logger = logging.getLogger(__name__)


class MessagingFactory:
    """
    Manages the lifecycle of messaging clients.
    Ensures a single Producer connection while allowing multiple Consumers.
    """

    _producer_instance: Optional[BaseProducer] = None

    @classmethod
    def get_producer(cls) -> BaseProducer:
        """
        Returns a singleton Producer instance.
        """
        if cls._producer_instance is None:
            broker_type = settings.MESSAGE_BROKER.lower()

            if broker_type == "kafka":
                cls._producer_instance = KafkaProducer()
            else:
                logger.error(f"❌ Unsupported message broker: {broker_type}")
                raise ValueError(f"Broker '{broker_type}' is not supported.")

        return cls._producer_instance

    @staticmethod
    def get_consumer(topic: str, group_id: str) -> KafkaConsumer:
        """
        Returns a NEW Kafka Consumer instance.
        Consumers are typically NOT singletons because different workers
        belong to different Consumer Groups.
        """
        broker_type = settings.MESSAGE_BROKER.lower()

        if broker_type == "kafka":
            return KafkaConsumer(topic=topic, group_id=group_id)

        raise ValueError(f"Consumer for '{broker_type}' is not supported.")


# --- Public API Hooks ---

# 1. Provide the singleton producer directly (for the Kafka Worker)
messaging_producer = MessagingFactory.get_producer()

# 2. Provide the functions (to match your 'from factory import get_producer' calls)
def get_producer():
    return MessagingFactory.get_producer()

def get_consumer(topic: str, group_id: str) -> KafkaConsumer:
    return MessagingFactory.get_consumer(topic, group_id)