import json
import logging
from typing import Any, Dict, Optional
from confluent_kafka import Producer, KafkaError
from streamlens_common.config.settings import GlobalSettings

# Initialize the shared logger we created earlier
logger = logging.getLogger(__name__)


class StreamLensProducer:
    def __init__(self, bootstrap_servers: str, client_id: str = "streamlens-generic-producer"):
        """
        Initializes the Kafka Producer with reliable defaults.
        """
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': client_id,
            'acks': 'all',  # Wait for all replicas to acknowledge
            'retries': 5,  # Retry on transient failures
            'compression.type': 'snappy'  # Better for log data throughput
        }
        self.producer = Producer(conf)

    def _delivery_report(self, err: Optional[KafkaError], msg: Any):
        """
        Callback triggered once for each message to indicate delivery result.
        """
        if err is not None:
            logger.error(f"Kafka delivery failed for record {msg.key()}: {err}")
        else:
            # Successfully delivered
            pass

    def send_message(self, topic: str, value: Dict[str, Any], key: Optional[str] = None):
        """
        Sends a message to Kafka asynchronously.
        """
        try:
            payload = json.dumps(value).encode('utf-8')

            self.producer.produce(
                topic=topic,
                key=key.encode('utf-8') if key else None,
                value=payload,
                on_delivery=self._delivery_report
            )

            # poll(0) serves delivery callbacks from previous calls
            # without blocking the current thread.
            self.producer.poll(0)

        except BufferError:
            logger.warning(f"Local producer queue is full ({len(self.producer)} messages awaiting delivery)")
            self.producer.flush()
        except Exception as e:
            logger.error(f"Unexpected error producing to Kafka: {e}")

    def flush(self, timeout: float = 10.0):
        """
        Ensure all messages are sent before shutting down.
        """
        logger.info("Flushing Kafka producer...")
        self.producer.flush(timeout)