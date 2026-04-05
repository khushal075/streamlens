"""
Messaging Factory
-----------------
Role: Handles the instantiation and retrieval of messaging providers.
Pattern: Factory / Singleton.
"""

import logging
from typing import Optional
from app.core.config import settings
from app.messaging.base.producer import BaseProducer
from app.messaging.kafka.kafka_producer import KafkaProducer

logger = logging.getLogger(__name__)


class MessagingFactory:
    """
    A factory class to manage and provide messaging producers.

    This ensures that we only ever have one producer instance (Singleton)
    active in our application memory, preventing multiple socket
    connections to the same broker.
    """

    _instance: Optional[BaseProducer] = None

    @classmethod
    def get_producer(cls) -> BaseProducer:
        """
        Returns the configured producer instance.
        Initializes it if it doesn't exist.
        """
        if cls._instance is None:
            broker_type = settings.MESSAGE_BROKER.lower()

            if broker_type == "kafka":
                cls._instance = KafkaProducer()
            # Future-proof: elif broker_type == "rabbitmq": ...
            else:
                logger.error(f"❌ Unsupported message broker: {broker_type}")
                raise ValueError(f"Broker '{broker_type}' is not supported.")

        return cls._instance


# --- Global Access Point ---
# Instead of calling the factory every time, we export the resulting instance.
messaging_producer = MessagingFactory.get_producer()