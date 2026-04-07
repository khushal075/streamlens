import os
import pytest
from unittest.mock import patch
# Import the CLASS so we can create fresh instances for testing
from app.core.config import IngestionSettings


def test_settings_default_values():
    """
    Verify the hardcoded defaults in the class.
    We pass _env_file=None to ensure this test doesn't accidentally
    pick up a local .env file, making it pass in CI and locally.
    """
    # Create a fresh instance that ignores any .env files
    settings = IngestionSettings(_env_file=None)

    # Your class 'app/core/config.py' defines BATCH_SIZE: int = 500
    # This is what will be used if no environment variable is set.
    assert settings.BATCH_SIZE == 500

    # These are inherited from GlobalSettings
    assert settings.CLICKHOUSE_BATCH_SIZE == 1000
    assert settings.PROJECT_NAME == "StreamLens Ingestion Service"


def test_settings_env_override():
    """Verify that Environment Variables correctly override defaults."""
    env_vars = {
        "PROJECT_NAME": "Override-Test",
        "BATCH_SIZE": "1000",
        "CLICKHOUSE_BATCH_SIZE": "2000"
    }

    # patch.dict injects these into the OS environment
    with patch.dict(os.environ, env_vars):
        # Again, ignore .env to ensure we are testing the OS ENV override
        settings = IngestionSettings(_env_file=None)

        assert settings.PROJECT_NAME == "Override-Test"
        assert settings.BATCH_SIZE == 1000
        assert settings.CLICKHOUSE_BATCH_SIZE == 2000


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