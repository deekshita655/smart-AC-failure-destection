from collections import Counter, defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.device import Device
from app.models.service_ticket import ServiceTicket
from app.models.predictive import DeviceHealth, Anomaly
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles

router = APIRouter(prefix="/analytics/devices", tags=["Device Analytics"])


def _month(value):
    return value.strftime("%Y-%m") if value else None


@router.get("/{device_id}", dependencies=[Depends(require_roles("TECHNICIAN"))])
def device_analytics(device_id: str, db: Session = Depends(get_db)):
    """Device-scoped analytics for the technician who identified a device."""
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Device not found.")

    tickets = (db.query(ServiceTicket)
               .filter(ServiceTicket.device_id == device.id)
               .order_by(desc(ServiceTicket.date)).all())

    component_counts = (db.query(ServiceTicket.technician_diagnosis_component, func.count())
                         .filter(ServiceTicket.device_id == device.id)
                         .group_by(ServiceTicket.technician_diagnosis_component).all())
    failure_mode_counts = (db.query(ServiceTicket.technician_diagnosis_failure_mode, func.count())
                            .filter(ServiceTicket.device_id == device.id)
                            .group_by(ServiceTicket.technician_diagnosis_failure_mode).all())
    severity_counts = (db.query(ServiceTicket.severity, func.count())
                       .filter(ServiceTicket.device_id == device.id)
                       .group_by(ServiceTicket.severity).all())

    health_records = (db.query(DeviceHealth)
                      .filter(DeviceHealth.device_id == device.id)
                      .order_by(DeviceHealth.timestamp.asc()).all())
    anomalies = (db.query(Anomaly)
                 .filter(Anomaly.device_id == device.id)
                 .order_by(Anomaly.detected_at.asc()).all())
    latest_health = health_records[-1] if health_records else None

    ticket_months = Counter()
    for ticket in tickets:
        period = _month(ticket.date)
        if period:
            ticket_months[period] += 1

    return success({
        "device_id": device.device_id,
        "total_service_tickets": len(tickets),
        "most_frequent_components": [
            {"component": c or "UNKNOWN", "count": n} for c, n in component_counts
        ],
        "most_frequent_failure_modes": [
            {"failure_mode": f or "UNKNOWN", "count": n} for f, n in failure_mode_counts
        ],
        "severity_distribution": [
            {"severity": s or "UNKNOWN", "count": n} for s, n in severity_counts
        ],
        "ticket_trends": [
            {"period": period, "count": count}
            for period, count in sorted(ticket_months.items())
        ],
        "recent_tickets": [{
            "ticket_id": t.ticket_id,
            "date": t.date,
            "symptom_text": t.symptom_text,
            "fix_text": t.fix_text,
            "status": t.status.value,
        } for t in tickets[:10]],
        "health": None if not latest_health else {
            "health_score": latest_health.health_score,
            "anomaly_score": latest_health.anomaly_score,
            "status": latest_health.status,
            "timestamp": latest_health.timestamp,
        },
        "health_history": [{
            "health_score": h.health_score,
            "anomaly_score": h.anomaly_score,
            "status": h.status,
            "timestamp": h.timestamp,
        } for h in health_records],
        "anomaly_history": [{
            "anomaly_score": a.anomaly_score,
            "description": a.description,
            "resolved": a.resolved,
            "detected_at": a.detected_at,
        } for a in anomalies],
    })
