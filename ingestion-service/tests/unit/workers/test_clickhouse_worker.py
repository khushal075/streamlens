import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.workers.clickhouse_worker import ClickHouseWorker


@pytest.mark.asyncio
async def test_clickhouse_worker_execution_loop():
    # 1. Setup Mocks
    mock_consumer = AsyncMock()

    # 2. Patch dependencies
    with patch("app.workers.clickhouse_worker.get_messaging_consumer", return_value=mock_consumer), \
            patch("app.workers.clickhouse_worker.storage_client") as mock_storage, \
            patch("app.workers.clickhouse_worker.settings") as mock_settings:
        mock_settings.CLICKHOUSE_BATCH_SIZE = 100
        mock_settings.KAFKA_STRUCTURED_TOPIC = "test-topic"

        worker = ClickHouseWorker()

        # 3. Smart Side Effect
        # This function tracks how many times it was called
        call_count = 0

        async def dynamic_fetch(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [{"log_id": "1", "message": "batch-1"}]

            # On second call, stop the loop and return empty
            worker.is_running = False
            return []

        mock_consumer.fetch_batch.side_effect = dynamic_fetch

        # 4. Execute
        await worker.start()

        # 5. Assertions
        assert mock_storage.connect.called
        assert mock_storage.insert_logs.called
        assert mock_consumer.commit.called
        assert worker.is_running is False