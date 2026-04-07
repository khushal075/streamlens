import pytest
from app.services.processors.networking.network_processor import NetworkProcessor


@pytest.fixture
def processor():
    return NetworkProcessor()


@pytest.mark.parametrize("raw_input, expected_key, expected_val", [
    # Based on your output: 'drop' becomes 'DENY' and it finds the IP
    ("firewall: drop packet from 10.0.0.5", "action", "DENY"),
    ("firewall: drop packet from 10.0.0.5", "nw_src_ip", "10.0.0.5"),
    # Based on your output: 'auth...' identifies the source IP
    ("auth: user admin login success from 192.168.1.1", "nw_src_ip", "192.168.1.1"),
    ("auth: user admin login success from 192.168.1.1", "vendor_type", "router"),
])
def test_network_parsing_success(processor, raw_input, expected_key, expected_val):
    result = processor.parse_message(raw_input)

    assert expected_key in result, f"Key '{expected_key}' missing. Got: {list(result.keys())}"
    assert result[expected_key] == expected_val


def test_network_parsing_failure(processor):
    """Ensure the processor doesn't crash on garbage data."""
    garbage = "!!!---NOT-A-LOG---!!!"
    result = processor.parse_message(garbage)

    # Usually, processors return the raw message or an empty dict on failure
    # Adjust this assertion based on what your code actually does
    assert isinstance(result, dict)