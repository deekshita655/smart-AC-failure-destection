"""
sensor_adapter - translates the simulator's JSON into the canonical
SensorReading fields. Keeps the simulator free to add/rename fields; unknown
fields are simply ignored rather than causing a validation failure.
"""
from datetime import datetime


def normalize_sensor_payload(raw: dict) -> dict:
    return {
        "device_id": raw.get("device_id"),
        "timestamp": raw.get("timestamp") or datetime.utcnow().isoformat(),
        "temperature": raw.get("temperature"),
        "compressor_current": raw.get("compressor_current"),
        "vibration": raw.get("vibration"),
        "fan_speed": raw.get("fan_speed"),
        "power_consumption": raw.get("power_consumption"),
        "refrigerant_pressure": raw.get("refrigerant_pressure"),
        "humidity": raw.get("humidity"),
    }
