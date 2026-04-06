"""
Storage Factory
---------------
Role: The 'Dispatcher' for Data Sinks.
Pattern: Factory / Singleton.
"""
import logging
from app.core.config import settings
from .clickhouse import ClickHouseStorage
from .s3_parquet import S3ParquetStorage

logger = logging.getLogger(__name__)


class StorageFactory:
    """
    Manages the lifecycle of database and object storage clients.
    """
    _clickhouse_instance = None
    _s3_instance = None

    @classmethod
    def get_client(cls):
        """
        Returns the primary storage client based on configuration.
        Movement: Kafka Topic --> ClickHouse Worker --> Storage Client
        """
        # Defaulting to ClickHouse for the 'Hot' path
        if cls._clickhouse_instance is None:
            logger.info("🏗️ Initializing ClickHouse Storage Client...")
            cls._clickhouse_instance = ClickHouseStorage()

        return cls._clickhouse_instance

    @classmethod
    def get_archiver(cls):
        """
        Returns the S3/Parquet archiver for the 'Cold' path.
        """
        if cls._s3_instance is None:
            logger.info("🏗️ Initializing S3 Parquet Archiver...")
            cls._s3_instance = S3ParquetStorage()

        return cls._s3_instance


# --- Global Instance for the Workers ---
storage_client = StorageFactory.get_client()