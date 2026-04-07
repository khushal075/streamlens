import pytest
from pydantic import ValidationError
# We import LogRequest because that's what exists in your app code
from app.models.log_model import LogRequest, LogEntry

def test_log_request_valid():
    """Test that a perfectly formed request passes validation."""
    data = {
        "tenant_id": "cust_123",
        "service": "nginx",
        "logs": [
            {"message": "127.0.0.1 GET /index.html", "timestamp": 1712445000}
        ]
    }
    # Changed LogBatch to LogRequest 👇
    request = LogRequest(**data)
    assert request.tenant_id == "cust_123"
    assert len(request.logs) == 1

def test_log_request_missing_fields():
    """Test that missing required fields raises a ValidationError."""
    invalid_data = {"tenant_id": "cust_123"} # Missing 'logs' and 'source'
    with pytest.raises(ValidationError):
        # Changed LogBatch to LogRequest 👇
        LogRequest(**invalid_data)

def test_log_request_empty_logs():
    """
    Test that an empty log list is rejected.
    """
    invalid_data = {
        "tenant_id": "cust_123",
        "source": "syslog",
        "logs": []
    }
    with pytest.raises(ValidationError):
        # Changed LogBatch to LogRequest 👇
        LogRequest(**invalid_data)

def test_log_entry_invalid_timestamp():
    """Test that non-integer timestamps are rejected."""
    invalid_entry = {
        "raw_payload": "some data",
        "timestamp": "not-a-unix-ts"
    }
    with pytest.raises(ValidationError):
        LogEntry(**invalid_entry)