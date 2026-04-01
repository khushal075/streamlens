# app/messaging/factory.py

from app.core.config import settings
from app.messaging.kafka.kafka_producer import KafkaProducer


def get_producer():
    if settings.MESSAGE_BROKER == "kafka":
        return KafkaProducer()

    raise ValueError("Unsupported broker")