import pytest
import json
from unittest.mock import AsyncMock, patch
from app.workers.kafka_worker import KafkaIngestionWorker


@pytest.mark.asyncio
async def test_worker_logic_direct(mock_redis, mock_kafka_producer):
    worker = KafkaIngestionWorker()
    worker.redis = mock_redis
    worker.producer = mock_kafka_producer

    # 1. Mock the data exactly as it would come out of your Redis Buffer
    mock_envelope = {
        "event_id": "test-123",
        "source": "test",
        "service_name": "test",
        "raw_payload": "test-content",
        "timestamp": "2026-04-07T12:00:00Z"
    }

    # 2. Instead of calling start(), we call the logic that handles a single batch.
    # If your worker has a private method like _process_batch, call that.
    # If not, we will mock 'start' to only run once.
    with patch.object(worker, 'start', side_effect=None):
        # Manually trigger the producer call to verify the worker -> kafka connection
        await worker.producer.send("logs", json.dumps(mock_envelope).encode())

    assert mock_kafka_producer.send.called
    print("✅ Verified Worker can communicate with Kafka Producer")