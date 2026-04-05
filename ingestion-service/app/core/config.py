"""
Settings Module
---------------
Role: The 'Source of Truth' for all environment-specific variables.
Pattern: Singleton / Data Transfer Object (DTO).
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Main Configuration Class.
    Uses Pydantic to automatically cast environment variables to the correct types.
    """

    # --- APP CONFIG ---
    PROJECT_NAME: str = "StreamLens Ingestion Service"
    DEBUG: bool = False

    # --- MESSAGE BROKER & QUEUE ---
    MESSAGE_BROKER: str = "kafka"
    MAX_QUEUE_SIZE: int = 10000
    BATCH_SIZE: int = 500
    WORKER_SLEEP_TIME: float = 0.05
    WORKER_THREADS: int = 4  # New: To control our ThreadPool size

    # --- KAFKA ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:29092"
    KAFKA_TOPIC: str = "logs"
    KAFKA_TOPIC_INGESTED: str = "ingested_logs"

    # --- REDIS ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_QUEUE_NAME: str = "log_queue"
    MAX_REDIS_CONNECTIONS: int = 100

    # Helper to generate the Redis URL
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # --- CLICKHOUSE ---
    # Adding these so your storage_service is also configurable
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DATABASE: str = "streamlens"

    # --- PYDANTIC CONFIG ---
    # This tells Pydantic to look for a .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Prevents crashing if extra vars are in .env
    )


# Create a single instance to be imported throughout the app
settings = Settings()