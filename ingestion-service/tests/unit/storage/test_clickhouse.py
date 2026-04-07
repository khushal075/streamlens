import pytest
from unittest.mock import MagicMock, patch
from app.storage.clickhouse import ClickHouseStorage


def test_clickhouse_storage_flow():
    # 1. Setup Mock Client
    mock_client = MagicMock()

    # 2. Patch the clickhouse_connect.get_client
    target = "app.storage.clickhouse.clickhouse_connect.get_client"

    with patch(target, return_value=mock_client):
        storage = ClickHouseStorage()

        # Test Connection (Covers lines 28-36 and _ensure_table 49-65)
        storage.connect()
        assert storage.client == mock_client
        # Verify the table creation query was sent
        assert mock_client.command.called

        # 3. Test insert_logs (Covers lines 74-102)
        # Matches your schema: timestamp, tenant_id, service, level, message, metadata
        test_batch = [{
            "timestamp": "2024-04-07 12:00:00",
            "tenant_id": 1,
            "service": "auth-api",
            "level": "INFO",
            "message": "User login success",
            "metadata": {"ip": "1.1.1.1"}
        }]

        storage.insert_logs(test_batch)

        # Verify ClickHouse bulk insert was called
        assert mock_client.insert.called
        args, kwargs = mock_client.insert.call_args
        assert args[0] == 'logs'  # Table name
        assert kwargs['column_names'][0] == 'timestamp'

        # Test Disconnect (Covers lines 43-46)
        storage.disconnect()
        assert mock_client.close.called