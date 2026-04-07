import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.workers.kafka_worker import KafkaIngestionWorker


@pytest.mark.asyncio
async def test_kafka_worker_full_loop_cycle():
    mock_producer = AsyncMock()
    mock_queue = AsyncMock()

    test_batch = [
        {"source": "syslog", "raw_payload": "test", "tenant_id": "101"}
    ]

    # 🔥 THE FIX: A generator that gives 1 batch, then empty lists forever
    def queue_behavior():
        yield test_batch
        while True:
            yield []

    mock_queue.pop_batch.side_effect = queue_behavior()
    mock_queue.connect = AsyncMock()
    mock_queue.disconnect = AsyncMock()

    # ... (rest of your patch logic) ...

    with patch("app.workers.kafka_worker.log_queue", mock_queue), \
            patch("app.workers.kafka_worker.get_producer", return_value=mock_producer), \
            patch("app.workers.kafka_worker.processor_factory"):

        worker = KafkaIngestionWorker()
        worker_task = asyncio.create_task(worker.start())

        # Let it process the 1st batch and spin on empty lists for a bit
        await asyncio.sleep(0.05)

        # Shutdown gracefully
        await worker.stop()

        # Cancel the task to be safe if stop() doesn't break the loop fast enough
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass

    # Now this will be true!
    assert mock_producer.send_batch.called