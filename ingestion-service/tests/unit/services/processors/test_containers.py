import pytest
import json
from app.services.processors.containers.base import ContainerBase


# 1. Create a concrete implementation for testing the base logic
class MockContainerProcessor(ContainerBase):
    def specialize(self, content: str):
        # Simple implementation to verify the content passed down
        return {"processed_content": content}


def test_container_base_json_parsing():
    """Targets lines 18-32: JSON wrapping and metadata extraction"""
    processor = MockContainerProcessor()

    # Test valid JSON wrapper (Common Docker/K8s format)
    raw_log = json.dumps({
        "container_id": "abc-123",
        "namespace": "prod",
        "log": "Hello World"
    })

    result = processor.parse_message(raw_log)

    assert result["container_id"] == "abc-123"
    assert result["namespace"] == "prod"
    assert result["processed_content"] == "Hello World"


def test_container_base_json_decode_error():
    """Targets lines 38-40: The exception fallback"""
    processor = MockContainerProcessor()

    # Non-JSON string to trigger JSONDecodeError
    raw_log = "Pure text log line"

    result = processor.parse_message(raw_log)

    # Should fallback to raw string and default metadata (None/default)
    assert result["processed_content"] == "Pure text log line"