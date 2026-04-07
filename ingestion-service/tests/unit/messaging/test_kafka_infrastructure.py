import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from app.messaging.kafka.kafka_producer import KafkaProducer


@pytest.mark.asyncio
async def test_kafka_producer_debug():
    # 1. The Patch
    target = "app.messaging.kafka.kafka_producer.AIOKafkaProducer"

    with patch(target) as mock_aio_class:
        mock_instance = AsyncMock()
        mock_aio_class.return_value = mock_instance

        # 2. THE DEBUG MOVE: Import inside the patch
        from app.messaging.kafka.kafka_producer import KafkaProducer
        producer = KafkaProducer()

        # --- DEBUG PRINT START ---
        print(f"\nDEBUG: Producer Type is {type(producer.producer)}")
        print(f"\nDEBUG: Is it a Mock? {producer.producer == mock_instance}")
        # --- DEBUG PRINT END ---

        await producer.start()

        # Act
        await producer.send_batch([{"id": 1}, {"id": 2}])

        print(f"DEBUG: Call count recorded: {mock_instance.send.call_count}")

        assert mock_instance.send.call_count == 2



@pytest.mark.asyncio
async def test_kafka_partition_key():
    """Verify the private partition key logic (Lines 117-121)."""
    producer = KafkaProducer()
    msg = {"tenant_id": "apple", "service": "ingestion"}
    key = producer._get_partition_key(msg)
    assert key == b"apple:ingestion"

@pytest.mark.asyncio
async def test_kafka_producer_unstarted_error():
    """Covers the RuntimeError line when producer is None."""
    producer = KafkaProducer()
    with pytest.raises(RuntimeError, match="Producer not started"):
        await producer.send_batch([{"data": 1}])