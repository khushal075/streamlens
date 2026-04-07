import pytest
from unittest.mock import patch, MagicMock
from app.messaging.factory import MessagingFactory
from app.messaging.base.producer import BaseProducer
from app.services.processors.factory import LogProcessorFactory, processor_factory


# --- 1. Abstract Interface Coverage ---

class ConcreteProducer(BaseProducer):
    """
    Satisfies ABC requirements. Calling super() executes the
    'pass' lines in base/producer.py (Reclaims 3-4 lines).
    """

    async def start(self):
        await super().start()

    async def stop(self):
        await super().stop()

    async def send_batch(self, messages):
        await super().send_batch(messages)


@pytest.mark.asyncio
async def test_base_producer_interface_coverage():
    """Triggers the 'pass' statements in the Abstract Base Class."""
    p = ConcreteProducer()
    await p.start()
    await p.stop()
    await p.send_batch([{"test": "data"}])


# --- 2. Factory Error Path Coverage ---

def test_messaging_factory_unsupported_broker():
    """
    Targets:
    - MessagingFactory.py Line 52 (get_producer error)
    - MessagingFactory.py Line 67 (get_consumer error)
    """
    # Reset singleton to force initialization
    MessagingFactory._producer_instance = None

    with patch("app.messaging.factory.settings") as mock_settings:
        mock_settings.MESSAGE_BROKER = "unsupported_vortex"

        # Hits Line 52
        with pytest.raises(ValueError, match="is not supported"):
            MessagingFactory.get_producer()

        # Hits Line 67
        with pytest.raises(ValueError, match="is not supported"):
            MessagingFactory.get_consumer(topic="test", group_id="test_group")


# --- 3. Singleton Logic ---

def test_messaging_factory_singleton_logic():
    """Covers the 'if _producer_instance is None' branch logic."""
    with patch("app.messaging.factory.KafkaProducer") as mock_kafka:
        # Reset to ensure we hit the 'is None' branch
        MessagingFactory._producer_instance = None

        p1 = MessagingFactory.get_producer()
        p2 = MessagingFactory.get_producer()

        assert p1 is p2
        # Ensures KafkaProducer() was only called once
        assert mock_kafka.call_count == 1


def test_log_processor_factory_logic():
    """
    Reclaims 3 lines in processors/factory.py:
    - The 'if not source' branch
    - The '.get()' fallback logic
    - The 'register_processor' method
    """
    # 1. Test empty source (Hits 'if not source')
    res = processor_factory.get_processor("")
    assert res == processor_factory.default_processor

    # 2. Test unknown source (Hits .get fallback)
    res = processor_factory.get_processor("unknown_service_xyz")
    assert res == processor_factory.default_processor

    # 3. Test registration (Hits register_processor and logger)
    class NewProcessor: pass
    processor_factory.register_processor("custom_source", NewProcessor())
    assert "custom_source" in processor_factory._registry



def test_processor_factory_logic_and_registration():
    """
    Targets LogProcessorFactory:
    - Empty source (if not source branch)
    - Unknown source (.get() default fallback)
    - register_processor method
    """
    # 1. Test empty source (Hits the 'if not source' branch)
    # Using the global instance 'processor_factory' from your file
    proc = processor_factory.get_processor("")
    assert proc == processor_factory.default_processor

    # 2. Test unknown source (Hits the .get() fallback)
    proc = processor_factory.get_processor("unknown_service_xyz")
    assert proc == processor_factory.default_processor

    # 3. Test registration (Hits the register_processor method)
    class FakeProc: pass
    processor_factory.register_processor("new_source", FakeProc())
    assert "new_source" in processor_factory._registry