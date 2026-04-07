import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.queue.redis_queue import RedisQueue


@pytest.mark.asyncio
async def test_enqueue_logic(mock_redis):
    # 💡 Tip: Ensure the path matches exactly where 'redis' is imported in redis_queue.py
    # If your file does 'import redis', use "app.queue.redis_queue.redis.Redis"
    # If your file does 'from redis import Redis', use "app.queue.redis_queue.Redis"
    with patch("app.queue.redis_queue.redis.Redis", return_value=mock_redis):
        queue = RedisQueue()
        # Initialize the connection if your class requires it
        if hasattr(queue, 'connect'):
            await queue.connect()

        test_data = [{"message": "hello", "tenant_id": "test_tenant"}]
        await queue.push_batch(test_data)

        # 💡 Check for BOTH rpush or lpush to be safe
        assert mock_redis.rpush.called or mock_redis.lpush.called


@pytest.mark.asyncio
async def test_redis_queue_operations():
    # 1. Setup the Mocks
    mock_redis_instance = AsyncMock()

    # We use MagicMock for the pipeline call because it
    # should return the context manager IMMEDIATELY, not as a coroutine.
    mock_pipeline = AsyncMock()
    mock_redis_instance.pipeline = MagicMock()

    # Setup the 'async with' behavior
    mock_redis_instance.pipeline.return_value.__aenter__.return_value = mock_pipeline
    mock_redis_instance.pipeline.return_value.__aexit__ = AsyncMock(return_value=None)

    # 2. Mock the Pipeline execution results
    fake_data = [json.dumps({"id": 1}), json.dumps({"id": 2})]
    mock_pipeline.execute.return_value = [fake_data, True]

    # 3. Patch the Redis CLASS
    target = "app.queue.redis_queue.redis.Redis"

    with patch(target, return_value=mock_redis_instance):
        queue = RedisQueue()

        # Connect
        await queue.connect()

        # 4. Act - This will now enter the 'async with' successfully
        batch = await queue.pop_batch(batch_size=2)

        # 5. Assert
        assert len(batch) == 2
        assert batch[0]["id"] == 1
        assert mock_pipeline.lrange.called
        assert mock_pipeline.ltrim.called

        # Bonus: Test push_batch to clear those lines too
        await queue.push_batch([{"id": 3}])
        assert mock_redis_instance.rpush.called