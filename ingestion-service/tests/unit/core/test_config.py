import os
import pytest
from unittest.mock import patch
# Import the CLASS so we can create fresh instances for testing
from app.core.config import IngestionSettings


def test_settings_default_values():
    """
    Verify the hardcoded defaults in the class.
    We clear the environment so CI variables (like BATCH_SIZE=1000)
    don't interfere with this specific test.
    """
    # clear=True temporarily hides ALL OS environment variables
    with patch.dict(os.environ, {}, clear=True):
        settings = IngestionSettings(_env_file=None)

        # This will now always be 500, because the environment is empty
        assert settings.BATCH_SIZE == 500
        assert settings.PROJECT_NAME == "StreamLens Ingestion Service"



def test_settings_env_override():
    """Verify that Environment Variables correctly override defaults."""
    env_vars = {
        "PROJECT_NAME": "Override-Test",
        "BATCH_SIZE": "1000"
    }

    with patch.dict(os.environ, env_vars):
        settings = IngestionSettings(_env_file=None)
        assert settings.PROJECT_NAME == "Override-Test"
        assert settings.BATCH_SIZE == 1000



def test_settings_validation_error():
    """Verify that invalid types raise a Pydantic ValidationError."""
    from pydantic import ValidationError

    # BATCH_SIZE is defined as an int, so passing a string should fail.
    with patch.dict(os.environ, {"BATCH_SIZE": "not-a-number"}):
        with pytest.raises(ValidationError):
            IngestionSettings(_env_file=None)


def test_redis_url_property():
    """Verify the dynamic REDIS_URL property logic."""
    settings = IngestionSettings(
        REDIS_HOST="test-redis",
        REDIS_PORT=6379,
        REDIS_DB=1,
        _env_file=None
    )
    assert settings.REDIS_URL == "redis://test-redis:6379/1"