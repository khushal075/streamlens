import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.buffer import LogBuffer


@pytest.mark.asyncio
async def test_log_buffer_flow():
    # 1. The Redis Client Mock
    # We use MagicMock for the client because pipeline() is a sync call
    mock_redis = MagicMock()

    # 2. Setup the Pipeline Mock
    # This is the secret sauce: pipeline() returns an object that
    # supports __aenter__ and __aexit__
    mock_pipe = AsyncMock()

    # Define the context manager behavior
    # When 'async with redis.pipeline()' is called:
    mock_redis.pipeline.return_value.__aenter__.return_value = mock_pipe

    # Setup what the pipeline returns after 'await pipe.execute()'
    mock_pipe.execute.return_value = [json.dumps({"id": 1, "msg": "test"})]

    # 3. Patch aioredis.from_url to return our mock_redis
    # Note: from_url IS a coroutine, so we use AsyncMock for the patch
    with patch("app.services.buffer.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_from_url.return_value = mock_redis

        buffer = LogBuffer(redis_url="redis://localhost:6379")

        # --- Test push_batch (Reclaims lines 32-46) ---
        # We need to make sure lpush is also an AsyncMock on our redis client
        mock_redis.lpush = AsyncMock()

        test_batch = [{"id": 1, "msg": "test"}]
        await buffer.push_batch(test_batch)
        assert mock_redis.lpush.called

        # --- Test dequeue_batch (Reclaims lines 68-74) ---
        results = await buffer.dequeue_batch(count=1)

        assert len(results) == 1
        assert results[0]["id"] == 1
        assert mock_pipe.rpop.called


@pytest.mark.asyncio
async def test_buffer_single_push_and_size():
    """Reclaims lines 59-64 (push) and 78-79 (size)"""
    mock_redis = MagicMock()
    mock_redis.lpush = AsyncMock()
    mock_redis.llen = AsyncMock(return_value=42)

    with patch("app.services.buffer.aioredis.from_url", new_callable=AsyncMock) as mock_from_url:
        mock_from_url.return_value = mock_redis
        buffer = LogBuffer()

        await buffer.push({"event": "single"})
        assert mock_redis.lpush.called

        size = await buffer.get_buffer_size()
        assert size == 42