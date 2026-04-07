import pytest
from unittest.mock import AsyncMock, patch
from app.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_storage_service_save_flow():
    """
    Tests the Librarian's role:
    1. Formatting dicts to tuples.
    2. Calling the ClickHouse client.
    """
    # 1. Setup the Mock for ClickHouseStorage
    # We use AsyncMock because save_logs uses 'await'
    mock_clickhouse_instance = AsyncMock()

    # 2. Patch the Class where it is imported in storage_service.py
    target = "app.services.storage_service.ClickHouseStorage"

    with patch(target, return_value=mock_clickhouse_instance):
        service = StorageService()

        # 3. Create dummy logs (The 'Flexible Processor Dictionaries')
        processed_logs = [
            {
                "timestamp": "2026-04-07 14:00:00",
                "tenant_id": 101,
                "service": "auth-api",
                "source": "kubernetes",
                "level": "ERROR",
                "message": "Connection Timeout",
                "metadata": {"node": "worker-1"}
            }
        ]

        # 4. Act: This triggers the private _prepare_for_clickhouse and the await
        # This will cover lines 38-57 and 66-81
        await service.save_logs(processed_logs)

        # 5. Assertions
        # Check if the mock was called (even if the method name in Storage is insert_logs,
        # your StorageService calls .insert_batch, so we mock that)
        assert mock_clickhouse_instance.insert_batch.called

        # Verify the Data Transformation Logic (The Tuple Schema)
        # Expected: (timestamp, tenant_id, service, source, level, message, metadata)
        call_args = mock_clickhouse_instance.insert_batch.call_args[0][0]
        row = call_args[0]

        assert isinstance(row, tuple)
        assert row[0] == "2026-04-07 14:00:00"  # timestamp
        assert row[1] == 101  # tenant_id
        assert row[4] == "ERROR"  # level
        assert row[6] == {"node": "worker-1"}  # metadata


@pytest.mark.asyncio
async def test_storage_service_empty_batch():
    """Covers the early return block (Line 71-72)"""
    mock_clickhouse = AsyncMock()
    with patch("app.services.storage_service.ClickHouseStorage", return_value=mock_clickhouse):
        service = StorageService()
        await service.save_logs([])
        assert not mock_clickhouse.insert_batch.called