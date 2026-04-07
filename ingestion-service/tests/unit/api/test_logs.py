from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

from unittest.mock import patch, AsyncMock

from unittest.mock import patch, AsyncMock
import pytest


def test_ingest_logs_success():
    # 💡 THE KEY: Patch the buffer inside the service, not just the API.
    # We also patch the rate_limiter to avoid any other Redis dependencies.
    with patch("app.services.ingestion_service.log_buffer") as mock_buffer, \
            patch("app.api.logs.log_buffer") as mock_api_buffer, \
            patch("app.api.logs.rate_limiter") as mock_limiter:
        # 1. Setup Buffer Mocks
        for b in [mock_buffer, mock_api_buffer]:
            b.get_buffer_size = AsyncMock(return_value=10)
            b.push_batch = AsyncMock(return_value=None)

        # 2. Setup Rate Limiter Mock
        mock_limiter.is_allowed = AsyncMock(return_value=True)

        valid_payload = {
            "tenant_id": "test_tenant",
            "service": "networking",
            "logs": [{"message": "kernel: eth0 up", "source": "test"}]
        }

        # This call will now stay entirely within the "Mock Universe"
        response = client.post("/api/v1/logs", json=valid_payload)

        assert response.status_code == 202
        assert "ingestion_id" in response.json()


def test_ingest_logs_invalid_payload():
    # Sending an empty list to trigger Pydantic validation error
    response = client.post("/api/v1/logs", json={"tenant_id": "t1", "logs": []})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_logs_rate_limited():
    with patch("app.api.logs.rate_limiter.is_allowed", AsyncMock(return_value=False)):
        response = client.post("/api/v1/logs", json={"tenant_id": "t1", "service": "s", "logs": []})
        assert response.status_code == 429

@pytest.mark.asyncio
async def test_ingest_logs_backpressure():
    with patch("app.api.logs.log_buffer.get_buffer_size", AsyncMock(return_value=999999)):
        response = client.post("/api/v1/logs", json={"tenant_id": "t1", "service": "s", "logs": []})
        assert response.status_code == 503


@pytest.mark.asyncio
async def test_ingest_logs_unexpected_failure():
    """Forces the API to hit the 'except Exception' block (Lines 64-66)."""
    from unittest.mock import patch, AsyncMock
    from app.api.logs import ingestion_service

    # We mock ingest_batch to raise a generic error
    with patch.object(ingestion_service, 'ingest_batch', side_effect=RuntimeError("Unexpected Crash")):
        # Ensure we pass the rate limit and buffer checks first
        with patch("app.api.logs.rate_limiter.is_allowed", AsyncMock(return_value=True)), \
                patch("app.api.logs.log_buffer.get_buffer_size", AsyncMock(return_value=0)):
            payload = {"tenant_id": "t1", "service": "s", "logs": [{"m": "test"}]}
            response = client.post("/api/v1/logs", json=payload)

            assert response.status_code == 500
            assert "Internal error" in response.json()["detail"]


def test_logs_endpoint_invalid_data():
    """Targets app/api/logs.py lines 48-49"""
    # Send an empty or completely wrong JSON to trigger the exception block
    response = client.post("/api/v1/logs", json={"wrong_key": "bad_value"})
    assert response.status_code in [400, 422]