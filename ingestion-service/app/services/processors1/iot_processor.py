import re
import logging
from typing import Dict, Any
from .base import BaseLogProcessor

logger = logging.getLogger(__name__)


class IoTProcessor(BaseLogProcessor):
    """
    Handles Logs from IoT Devices, Sensors, and Gateways.
    Category: IoT Device Logs (Telemetry, Health, Sensor Readings)
    """

    # Matches: temp=22.5, hum=60, volt=3.3 or DEVICE:001 STATUS:OK
    IOT_KV_PATTERN = re.compile(r'(?P<key>\w+)[:=](?P<value>[\d\.]+|\w+)')

    def process(self, raw_data: str) -> Dict[str, Any]:
        if not self._validate_input(raw_data):
            return self._create_fallback(raw_data, "empty_iot_payload")

        try:
            # 1. Extract Key-Value Pairs
            matches = self.IOT_KV_PATTERN.findall(raw_data)
            telemetry = {}

            for k, v in matches:
                key = k.lower()
                # Try to convert to float/int if numeric
                try:
                    if '.' in v:
                        telemetry[key] = float(v)
                    else:
                        telemetry[key] = int(v)
                except ValueError:
                    telemetry[key] = v

            # 2. Determine Health Status
            level = "INFO"
            if telemetry.get("status") in ["CRIT", "ERR", "LOW_BATT"] or telemetry.get("temp", 0) > 80:
                level = "ERROR"

            return {
                "timestamp": self.get_utc_now(),
                "level": level,
                "message": f"Telemetry from {telemetry.get('device_id', 'unknown_device')}",
                "metadata": {
                    **telemetry,
                    "parser": "iot_telemetry_v1",
                    "is_telemetry": True
                }
            }

        except Exception as e:
            logger.error(f"IoTProcessor Error: {e}")
            return self._create_fallback(raw_data, "iot_parse_exception")