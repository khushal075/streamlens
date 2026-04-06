"""
Kafka Consumer Module
---------------------
Role: The 'Drain' of the messaging pipeline.
Purpose: Pulls processed logs from Kafka topics for permanent storage.
Movement: Kafka Topic --> DB Worker --> ClickHouse
"""

import logging
import json
from typing import List, Dict, Any, Optional
from aiokafka import AIOKafkaConsumer
from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaConsumer:
    """
    A high-level wrapper around AIOKafkaConsumer tailored for StreamLens.

    This class handles the 'Movement B' phase of the pipeline:
    1. Subscribes to a specific Kafka Topic (e.g., 'transformed_logs').
    2. Joins a Consumer Group to allow for horizontal scaling.
    3. Provides batch-fetching capabilities to optimize ClickHouse inserts.

    Attributes:
        topic (str): The Kafka topic to consume from.
        group_id (str): The consumer group ID for offset management.
        bootstrap_servers (str): Connection string for the Kafka cluster.
    """

    def __init__(self, topic: str, group_id: str):
        """
        Initializes the consumer configuration.

        Args:
            topic (str): The target Kafka topic.
            group_id (str): Ensures that logs are distributed across worker instances.
        """
        self.topic = topic
        self.group_id = group_id
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.consumer: Optional[AIOKafkaConsumer] = None

    async def start(self) -> None:
        """
        Starts the asynchronous Kafka consumer and joins the group.

        This should be called during the DB Worker's startup phase.
        """
        try:
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                # Start from the earliest message if no offset is found
                auto_offset_reset='earliest',
                # Disable auto-commit to ensure 'At Least Once' delivery to the DB
                enable_auto_commit=False,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            await self.consumer.start()
            logger.info(f"📥 Kafka Consumer started: Topic={self.topic}, Group={self.group_id}")
        except Exception as e:
            logger.error(f"❌ Failed to start Kafka Consumer: {e}")
            raise

    async def stop(self) -> None:
        """Gracefully shuts down the consumer connection."""
        if self.consumer:
            await self.consumer.stop()
            logger.info(f"🛑 Kafka Consumer stopped for topic {self.topic}")

    async def get_batch(self, max_records: int = 500, timeout_ms: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetches a batch of messages from Kafka.

        This is crucial for the 'DB Worker' to perform high-speed bulk
        inserts into ClickHouse rather than row-by-row writes.

        Args:
            max_records (int): Maximum logs to pull in one go.
            timeout_ms (int): How long to wait for data before returning an empty list.

        Returns:
            List[Dict]: A list of deserialized log envelopes.
        """
        if not self.consumer:
            return []

        # Pull multiple records from assigned partitions
        batch = await self.consumer.getmany(
            timeout_ms=timeout_ms,
            max_records=max_records
        )

        # Flatten the dictionary {TopicPartition: [Messages]} into a simple list
        logs = []
        for tp, messages in batch.items():
            for msg in messages:
                logs.append(msg.value)

        return logs

    async def commit(self) -> None:
        """
        Manually commits the offsets to Kafka.

        Should be called by the DB Worker ONLY after ClickHouse
        confirms a successful batch insertion.
        """
        if self.consumer:
            await self.consumer.commit()