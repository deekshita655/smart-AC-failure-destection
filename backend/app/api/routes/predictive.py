from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.device import Device
from app.models.predictive import DeviceHealth, Anomaly, PredictiveEvent, PreventiveTicket
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles
from sqlalchemy import func

router = APIRouter(prefix="/predictive", tags=["Predictive Maintenance"])


@router.get("/overview", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def predictive_overview(db: Session = Depends(get_db)):
    devices = {d.id: d.device_id for d in db.query(Device).all()}
    latest = db.query(DeviceHealth).order_by(DeviceHealth.timestamp.desc()).limit(500).all()
    latest_by_device = {}
    for row in latest:
        latest_by_device.setdefault(row.device_id, row)

    health = [{
        "device_id": devices.get(row.device_id), "health_score": row.health_score,
        "anomaly_score": row.anomaly_score, "status": row.status, "timestamp": row.timestamp,
    } for row in latest_by_device.values()]
    health_history = db.query(DeviceHealth).order_by(DeviceHealth.timestamp.asc()).limit(1000).all()
    history = [{
        "device_id": devices.get(row.device_id), "health_score": row.health_score,
        "anomaly_score": row.anomaly_score, "status": row.status, "timestamp": row.timestamp,
    } for row in health_history]
    risk = db.query(PredictiveEvent.risk_level, func.count()).group_by(PredictiveEvent.risk_level).order_by(func.count().desc()).all()
    outcomes = db.query(PredictiveEvent.actual_outcome, func.count()).group_by(PredictiveEvent.actual_outcome).all()
    predictions = db.query(PredictiveEvent).order_by(PredictiveEvent.timestamp.desc()).limit(20).all()
    anomalies = db.query(Anomaly).order_by(Anomaly.detected_at.desc()).limit(20).all()

    return success({
        "health": health,
        "health_history": history,
        "risk_distribution": [{"risk_level": r or "PENDING", "count": n} for r, n in risk],
        "outcome_distribution": [{"outcome": o or "PENDING", "count": n} for o, n in outcomes],
        "predictions": [{"device_id": devices.get(p.device_id), "predicted_issue": p.predicted_issue,
                         "confidence": p.confidence, "risk_level": p.risk_level,
                         "actual_outcome": p.actual_outcome, "timestamp": p.timestamp} for p in predictions],
        "anomalies": [{"device_id": devices.get(a.device_id), "anomaly_score": a.anomaly_score,
                       "description": a.description, "resolved": a.resolved, "detected_at": a.detected_at} for a in anomalies],
        "preventive_tickets": db.query(func.count(PreventiveTicket.id)).scalar() or 0,
    })


@router.get("/predictions/outcomes", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def prediction_outcomes(db: Session = Depends(get_db)):
    rows = db.query(PredictiveEvent.actual_outcome, func.count()).group_by(PredictiveEvent.actual_outcome).all()
    return success([{"outcome": o or "PENDING", "count": n} for o, n in rows])


@router.get("/{device_id}/health", dependencies=[Depends(require_roles(
    "TECHNICIAN", "OVERALL_MANAGEMENT", "DESIGN"))])
def current_health(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Device not found.")
    latest = db.query(DeviceHealth).filter(DeviceHealth.device_id == device.id).order_by(DeviceHealth.timestamp.desc()).first()
    if not latest:
        return success(None)
    return success({"device_id": device_id, "health_score": latest.health_score,
                    "anomaly_score": latest.anomaly_score, "status": latest.status, "timestamp": latest.timestamp})


@router.get("/{device_id}/anomalies", dependencies=[Depends(require_roles(
    "OVERALL_MANAGEMENT", "TECHNICIAN"))])
def anomalies(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Device not found.")
    rows = db.query(Anomaly).filter(Anomaly.device_id == device.id).order_by(Anomaly.detected_at.desc()).all()
    return success([{"id": a.id, "detected_at": a.detected_at, "anomaly_score": a.anomaly_score,
                     "description": a.description, "resolved": a.resolved} for a in rows])


@router.get("/{device_id}/predictions", dependencies=[Depends(require_roles(
    "OVERALL_MANAGEMENT", "TECHNICIAN"))])
def predictions(device_id: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Device not found.")
    rows = db.query(PredictiveEvent).filter(PredictiveEvent.device_id == device.id).order_by(PredictiveEvent.timestamp.desc()).all()
    return success([{"id": p.id, "timestamp": p.timestamp, "predicted_issue": p.predicted_issue,
                     "confidence": p.confidence, "risk_level": p.risk_level, "actual_outcome": p.actual_outcome} for p in rows])
