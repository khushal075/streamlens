import re
from typing import Dict, Any
from ..base import BaseLogProcessor


class IoTBase(BaseLogProcessor):
    """
    Parent: Logic for Industrial Sensors, Gateways, and Telemetry.
    Focuses on Device Identification and Metric Units.
    """
    # Regex to find UUIDs or MAC Addresses (common for IoT devices)
    DEVICE_ID_PATTERN = re.compile(r'\b([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})\b|\bdev_[a-zA-Z0-9]{8,}\b')
    # Regex to find numbers followed by units (e.g., 22.5C, 80%, 12V)
    METRIC_PATTERN = re.compile(r'(\d+\.?\d*)\s*([a-zA-Z%]+)')

    def extract_telemetry(self, message: str) -> Dict[str, Any]:
        """
        Utility: Extracts the Device ID and the primary reading.
        """
        device_match = self.DEVICE_ID_PATTERN.search(message)
        metric_match = self.METRIC_PATTERN.search(message)

        return {
            "device_id": device_match.group(0) if device_match else "unknown_sensor",
            "value": float(metric_match.group(1)) if metric_match else 0.0,
            "unit": metric_match.group(2) if metric_match else "raw"
        }