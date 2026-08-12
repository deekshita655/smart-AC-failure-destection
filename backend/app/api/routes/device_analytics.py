from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.core.database import get_db
from app.models.device import Device
from app.models.service_ticket import ServiceTicket
from app.models.predictive import DeviceHealth
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles

router = APIRouter(prefix="/analytics/devices", tags=["Device Analytics"])


@router.get("/{device_id}", dependencies=[Depends(require_roles("TECHNICIAN"))])
def device_analytics(device_id: str, db: Session = Depends(get_db)):
    """
    Limited, device-scoped analytics for the technician who just identified a
    device - distinct from manufacturer-wide analytics (see manufacturer_analytics.py).
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Device not found.")

    tickets = db.query(ServiceTicket).filter(ServiceTicket.device_id == device.id).all()

    component_counts = (db.query(ServiceTicket.technician_diagnosis_component, func.count())
                         .filter(ServiceTicket.device_id == device.id)
                         .group_by(ServiceTicket.technician_diagnosis_component).all())
    failure_mode_counts = (db.query(ServiceTicket.technician_diagnosis_failure_mode, func.count())
                            .filter(ServiceTicket.device_id == device.id)
                            .group_by(ServiceTicket.technician_diagnosis_failure_mode).all())
    severity_counts = (db.query(ServiceTicket.severity, func.count())
                        .filter(ServiceTicket.device_id == device.id)
                        .group_by(ServiceTicket.severity).all())

    latest_health = (db.query(DeviceHealth).filter(DeviceHealth.device_id == device.id)
                      .order_by(desc(DeviceHealth.timestamp)).first())

    return success({
        "device_id": device.device_id,
        "total_service_tickets": len(tickets),
        "most_frequent_components": [{"component": c or "UNKNOWN", "count": n} for c, n in component_counts],
        "most_frequent_failure_modes": [{"failure_mode": f or "UNKNOWN", "count": n} for f, n in failure_mode_counts],
        "severity_distribution": [{"severity": s or "UNKNOWN", "count": n} for s, n in severity_counts],
        "recent_tickets": [{
            "ticket_id": t.ticket_id, "date": t.date, "symptom_text": t.symptom_text,
            "fix_text": t.fix_text, "status": t.status.value,
        } for t in sorted(tickets, key=lambda t: t.date, reverse=True)[:10]],
        "health": None if not latest_health else {
            "health_score": latest_health.health_score,
            "anomaly_score": latest_health.anomaly_score,
            "status": latest_health.status,
            "timestamp": latest_health.timestamp,
        },
    })
