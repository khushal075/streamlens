import pytest
from app.services.processors.factory import processor_factory


@pytest.mark.parametrize("source_key", [
    "firewall", "kubernetes", "postgresql", "nginx",
    "aws", "auth", "syslog", "stripe", "sensor", "generic"
])
def test_all_processors_via_factory(source_key):
    # 1. Get the specialized processor from the global factory instance
    processor = processor_factory.get_processor(source_key)

    # 2. Create the exact structure process_batch expects
    # It looks for a "logs" list containing "message" keys
    dummy_envelope = {
        "tenant_id": "tenant-123",
        "source": source_key,
        "logs": [
            # 1. Temperature + Overheating Alert (Value > 50.0)
            {"message": "Device dev_A1B2C3D4 reporting 65.5 C", "timestamp": 1712490000},

            # 2. Humidity branch
            {"message": "Sensor hum_99 reported 42% humidity", "timestamp": 1712490001},

            # 3. Power + Low Power Alert (Value < 5.0)
            {"message": "Gateway dev_power_01 voltage at 4.2V", "timestamp": 1712490002},

            # 4. Networking/Security strings (triggers logic in those folders)
            {"message": "Accepted password for root from 192.168.1.1 port 22 ssh2"},

            # 5. The "Empty" logic (Covers line 32-34 in base.py)
            {"message": "   "},

            # 6. The "Exception" logic (Covers lines 47-48 in base.py)
            # We pass a non-string to trigger the 'raw_msg.get' failure if applicable
            {}
        ]
    }

    # 3. Trigger the Template Method
    # This hits BaseLogProcessor.process_batch -> IoTProcessor.parse_message -> IoTBase.extract_telemetry
    results = processor.process_batch(dummy_envelope)

    # 4. Assertions to ensure the pipe worked
    assert isinstance(results, list)
    assert len(results) == 6
    assert "log_id" in results[0]
    assert results[0]["tenant_id"] == "tenant-123"