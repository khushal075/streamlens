import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(autouse=True)
async def cleanup_connections():
    yield
    from app.services.buffer import log_buffer
    if log_buffer.redis:
        await log_buffer.redis.close()

@pytest.fixture
def mock_redis():
    """Mock for Redis Queue operations."""
    mock = AsyncMock()
    mock.rpush = AsyncMock(return_value=1)
    mock.lpop = AsyncMock(return_value=None)
    return mock

@pytest.fixture
def mock_kafka_producer():
    """Mock for Kafka Producer."""
    mock = AsyncMock()
    mock.send_and_wait = AsyncMock()
    return mock

@pytest.fixture
def sample_log_payload():
    """Standard payload for API testing."""
    return {
        "tenant_id": "test_tenant",
        "source": "networking",
        "logs": [{"raw_payload": "kernel: eth0 up", "timestamp": 1712445000}]
    }
