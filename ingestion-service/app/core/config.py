from streamlens_common import GlobalSettings
from pydantic_settings import SettingsConfigDict

class IngestionSettings(GlobalSettings):
    """
    Child DTO: Specific to the Ingestion Service.
    Inherits all Kafka, Redis, and ClickHouse settings from Global.
    """
    # --- APP CONFIG OVERRIDE ---
    PROJECT_NAME: str = "StreamLens Ingestion Service"

    # --- MESSAGE BROKER & QUEUE LOGIC ---
    MESSAGE_BROKER: str = "kafka"
    MAX_QUEUE_SIZE: int = 10000
    BATCH_SIZE: int = 500
    WORKER_SLEEP_TIME: float = 0.05
    WORKER_THREADS: int = 4

    # --- REDIS SPECIFICS ---
    REDIS_QUEUE_NAME: str = "log_queue"
    MAX_REDIS_CONNECTIONS: int = 100

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Ensure local .env also takes priority here
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# --- SINGLETON INSTANCE ---
# Your workers/API will import THIS object.
settings = IngestionSettings()