from .base import IoTBase
from typing import Dict, Any


class IoTProcessor(IoTBase):
    """
    Child: Specific logic for Temperature, Humidity, and Power sensors.
    """

    def parse_message(self, raw_message: str) -> Dict[str, Any]:
        # 1. Get the Telemetry from Parent
        telemetry = self.extract_telemetry(raw_message)

        # 2. Logic: Identify Sensor Category and Alert Level
        msg_lower = str(raw_message).lower()
        sensor_type = "generic_sensor"
        is_alert = False

        if "temp" in msg_lower or "c" in telemetry["unit"].lower():
            sensor_type = "temperature"
            if telemetry["value"] > 50.0: is_alert = True  # Overheating
        elif "hum" in msg_lower or "%" in telemetry["unit"]:
            sensor_type = "humidity"
        elif "volt" in msg_lower or "v" in telemetry["unit"].lower():
            sensor_type = "power"
            if telemetry["value"] < 5.0: is_alert = True  # Low Power

        return {
            **telemetry,
            "sensor_type": sensor_type,
            "status": "CRITICAL" if is_alert else "OK",
            "is_telemetry_valid": telemetry["device_id"] != "unknown_sensor"
        }