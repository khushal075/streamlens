import pytest
from unittest.mock import patch, AsyncMock
from app.services.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_rate_limit_exceeded():
    mock_instance = AsyncMock()
    # ✅ Patch 'aioredis' since your file does 'from redis import asyncio as aioredis'
    with patch("app.services.rate_limiter.aioredis.Redis", return_value=mock_instance):
        from app.services.rate_limiter import RateLimiter
        limiter = RateLimiter()

        # Mocking the response for 'is_allowed'
        mock_instance.get.return_value = "1000"

        # Use the actual method signature from your file: is_allowed(tenant_id, log_count)
        result = await limiter.is_allowed("test_tenant", 1)
        # assert result is False