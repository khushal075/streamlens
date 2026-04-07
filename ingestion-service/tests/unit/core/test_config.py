import os
import pytest
from unittest.mock import patch
from app.core.config import IngestionSettings


def test_settings_default_values():
    from app.core.config import settings

    # This is the 'BATCH_SIZE' defined in IngestionSettings
    assert settings.BATCH_SIZE == 1000

    # This is inherited from GlobalSettings
    assert settings.CLICKHOUSE_BATCH_SIZE == 1000

    # Verify the override worked
    assert settings.PROJECT_NAME == "StreamLens Ingestion Service"


def test_settings_env_override():
    """Verify that Environment Variables correctly override defaults."""
    env_vars = {
        "PROJECT_NAME": "Override-Test",
        "BATCH_SIZE": "999"
    }

    with patch.dict(os.environ, env_vars):
        settings = IngestionSettings()
        assert settings.PROJECT_NAME == "Override-Test"
        assert settings.BATCH_SIZE == 999


def test_settings_validation_error():
    """Verify that invalid types raise a Pydantic ValidationError."""
    from pydantic import ValidationError

    # 💡 Pydantic validates fields it knows. 'BATCH_SIZE' is an Int.
    with patch.dict(os.environ, {"BATCH_SIZE": "not-a-number"}):
        with pytest.raises(ValidationError):
            # We must instantiate to trigger validation
            IngestionSettings()


def test_get_database_url_logic():
    """Verify ClickHouse URL generation if applicable."""
    settings = IngestionSettings()
    # If your IngestionSettings has a property called CLICKHOUSE_URL
    # that combines host, user, and password, test it here.
    # assert "localhost" in settings.CLICKHOUSE_URL
    pass