import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock, MagicMock
from contextlib import ExitStack


def test_health_check_complete():
    # We patch log_buffer because health_check calls log_buffer.get_buffer_size()
    with patch("app.main.log_buffer") as mock_buffer:
        mock_buffer.get_buffer_size = AsyncMock(return_value=100)

        # Use TestClient without 'with' to avoid lifespan/signal errors
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["buffer_size"] == 100


def test_health_check_simple():
    with patch("app.main.log_buffer") as mock_buffer:
        mock_buffer.get_buffer_size = AsyncMock(return_value=0)
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_app_lifespan_coverage():
    """Forces execution of every line in main.py's lifespan (Startup & Shutdown)."""
    from app.main import lifespan

    mock_app = MagicMock()
    mock_app.state = MagicMock()

    mock_buffer = MagicMock()
    mock_buffer.connect = AsyncMock()
    mock_buffer.disconnect = AsyncMock()

    # Create a mock task that actually responds to .cancel()
    mock_task = AsyncMock(spec=asyncio.Task)

    patches = [
        patch("app.main.log_buffer", mock_buffer),
        patch("app.main.kafka_ingestion_worker", return_value=AsyncMock()),
        patch("app.main.ch_worker", return_value=AsyncMock()),
        patch("app.main.asyncio.create_task", return_value=mock_task),
        # We also need to mock wait_for so it doesn't actually wait 5 seconds
        patch("app.main.asyncio.wait_for", AsyncMock())
    ]

    with ExitStack() as stack:
        for p in patches:
            stack.enter_context(p)

        async with lifespan(mock_app):
            # STARTUP logic is covered here
            pass

            # SHUTDOWN logic is covered here after the 'with' block exits
        assert mock_buffer.disconnect.called


def test_main_app_initialization():
    """Reclaims lines 59-60 in app/main.py"""
    # Verify the app loaded
    assert app.title is not None

    # Use the correct route name found in your error log
    route_names = [route.name for route in app.routes]
    assert "ingest_logs" in route_names
    assert "health_check" in route_names