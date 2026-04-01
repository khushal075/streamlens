# app/core/config.py

import os


class Settings:
    MESSAGE_BROKER = os.getenv("MESSAGE_BROKER", "kafka")

    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "logs")

    MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", 10000))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", 500))

    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_QUEUE_NAME = "log_queue"


# ✅ THIS LINE IS REQUIRED
settings = Settings()