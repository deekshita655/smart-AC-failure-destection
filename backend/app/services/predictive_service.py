"""
PredictiveService - MVP heuristic health/anomaly scoring over simulated sensor
streams. This is intentionally simple (not a trained model) so the digital-twin
loop is demonstrable end-to-end; it can be swapped for a real model later
without changing the API contract (see app.integrations.sensor_adapter).
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.predictive import SensorReading, DeviceHealth, Anomaly, PredictiveEvent, PreventiveTicket
from app.models.device import Device
from app.models.enums import DeviceHealthStatus, PreventiveTicketStatus
from app.core.config import settings

# "Normal" baseline ranges used purely for MVP heuristic scoring.
BASELINES = {
    "temperature": (18, 26),
    "compressor_current": (3, 8),
    "vibration": (0, 2.5),
    "fan_speed": (600, 1400),
    "power_consumption": (800, 1600),
    "refrigerant_pressure": (100, 160),
    "humidity": (30, 60),
}


def _deviation_score(value, lo, hi) -> float:
    if value is None:
        return 0.0
    if lo <= value <= hi:
        return 0.0
    span = max(hi - lo, 1e-6)
    return min(1.0, abs(value - (lo if value < lo else hi)) / span)


def compute_health(reading: SensorReading) -> tuple[float, float, str]:
    deviations = []
    for field, (lo, hi) in BASELINES.items():
        deviations.append(_deviation_score(getattr(reading, field), lo, hi))
    anomaly_score = round(sum(deviations) / len(deviations), 4)
    health_score = round(max(0.0, 100.0 - anomaly_score * 100.0), 2)

    if anomaly_score >= 0.85:
        status = DeviceHealthStatus.CRITICAL.value
    elif anomaly_score >= settings.PREDICTIVE_ANOMALY_THRESHOLD:
        status = DeviceHealthStatus.ANOMALOUS.value
    elif anomaly_score >= 0.35:
        status = DeviceHealthStatus.DEGRADING.value
    else:
        status = DeviceHealthStatus.HEALTHY.value

    return health_score, anomaly_score, status


def process_reading(db: Session, reading: SensorReading) -> DeviceHealth:
    health_score, anomaly_score, status = compute_health(reading)

    health = DeviceHealth(
        device_id=reading.device_id,
        timestamp=reading.timestamp,
        health_score=health_score,
        anomaly_score=anomaly_score,
        status=status,
    )
    db.add(health)

    if status in (DeviceHealthStatus.ANOMALOUS.value, DeviceHealthStatus.CRITICAL.value):
        db.add(Anomaly(
            device_id=reading.device_id,
            detected_at=reading.timestamp,
            anomaly_score=anomaly_score,
            description=f"Anomaly detected (status={status}, anomaly_score={anomaly_score})",
        ))

    predicted_issue = None
    risk_level = None
    if health_score <= settings.PREDICTIVE_HEALTH_THRESHOLD:
        risk_level = "CRITICAL" if status == DeviceHealthStatus.CRITICAL.value else "HIGH"
        predicted_issue = "Potential compressor / refrigerant-system degradation" \
            if (reading.vibration or 0) > BASELINES["vibration"][1] else "Potential efficiency degradation"

        event = PredictiveEvent(
            device_id=reading.device_id,
            timestamp=reading.timestamp,
            predicted_issue=predicted_issue,
            confidence=round(anomaly_score, 2),
            risk_level=risk_level,
            actual_outcome="PENDING",
        )
        db.add(event)
        db.flush()

        db.add(PreventiveTicket(
            device_id=reading.device_id,
            predictive_event_id=event.id,
            status=PreventiveTicketStatus.PENDING.value,
            created_at=datetime.now(timezone.utc),
        ))

    db.commit()
    db.refresh(health)
    return health
