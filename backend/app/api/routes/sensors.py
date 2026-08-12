from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.device import Device
from app.models.predictive import SensorReading
from app.schemas.sensor import SensorReadingIn
from app.integrations.sensor_adapter import normalize_sensor_payload
from app.services.predictive_service import process_reading
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles

router = APIRouter(prefix="/sensors", tags=["Sensor Simulation"])


@router.post("/readings", dependencies=[Depends(require_roles("ADMIN", "TECHNICIAN"))])
def ingest_reading(payload: SensorReadingIn, db: Session = Depends(get_db)):
    """
    Receives one simulated sensor reading directly from the Python simulator
    (no IoT Hub / Event Hub). Immediately computes health/anomaly scores and,
    if the configured threshold is crossed, creates a PENDING preventive ticket.
    """
    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Cannot ingest a reading for an unknown device.")

    normalized = normalize_sensor_payload(payload.model_dump())
    reading = SensorReading(device_id=device.id, timestamp=normalized["timestamp"],
                             temperature=normalized["temperature"],
                             compressor_current=normalized["compressor_current"],
                             vibration=normalized["vibration"], fan_speed=normalized["fan_speed"],
                             power_consumption=normalized["power_consumption"],
                             refrigerant_pressure=normalized["refrigerant_pressure"],
                             humidity=normalized["humidity"])
    db.add(reading)
    db.flush()

    health = process_reading(db, reading)
    return success({
        "device_id": device.device_id, "health_score": health.health_score,
        "anomaly_score": health.anomaly_score, "status": health.status,
    }, status_code=201)


@router.get("/{device_id}/history")
def sensor_history(device_id: str, db: Session = Depends(get_db), user=Depends(require_roles(
        "TECHNICIAN", "OVERALL_MANAGEMENT", "DESIGN"))):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Device not found.")
    readings = (db.query(SensorReading).filter(SensorReading.device_id == device.id)
                .order_by(SensorReading.timestamp.desc()).limit(200).all())
    return success([{
        "timestamp": r.timestamp, "temperature": r.temperature,
        "compressor_current": r.compressor_current, "vibration": r.vibration,
        "fan_speed": r.fan_speed, "power_consumption": r.power_consumption,
        "refrigerant_pressure": r.refrigerant_pressure, "humidity": r.humidity,
    } for r in readings])
