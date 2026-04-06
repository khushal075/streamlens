from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class GlobalSettings(BaseSettings):
    """
    Common Infrastructure 'Source of Truth'.
    Shared by all StreamLens microservices.
    """
    # --- PROJECT INFO ---
    PROJECT_NAME: str = "StreamLens"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # --- KAFKA ---
    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="localhost:9092", alias="KAFKA_SERVERS")
    KAFKA_TOPIC_RAW: str = "logs.raw"
    KAFKA_TOPIC_INGESTED: str = "ingested_logs"

    # --- REDIS ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # --- CLICKHOUSE ---
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DATABASE: str = "streamlens"

    # This is the "Magic" part. It tells child classes to look for a .env file
    # in their current working directory.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )