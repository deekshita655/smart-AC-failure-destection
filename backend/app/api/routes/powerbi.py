from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.predictive import DeviceHealth, Anomaly, PreventiveTicket, PredictiveEvent
from app.utils.responses import success
from app.auth.deps import require_roles

router = APIRouter(prefix="/powerbi", tags=["Power BI Data Access"])

# These are READ-ONLY, flattened, PII-free analytical endpoints intended to be
# queried by Power BI (Web/REST connector) on a schedule. Power BI never calls
# Azure OpenAI or Gemini directly - it only reads pre-computed data from here.


@router.get("/dataset/service-tickets", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT", "ADMIN"))])
def dataset_service_tickets(db: Session = Depends(get_db)):
    rows = (db.query(ServiceTicket, Device)
            .join(Device, ServiceTicket.device_id == Device.id).all())
    return success([{
        "ticket_id": t.ticket_id, "date": t.date, "product_model": d.product_model,
        "serial_range": d.serial_range, "failure_mode": t.technician_diagnosis_failure_mode,
        "component": t.technician_diagnosis_component, "department": t.technician_diagnosis_department,
        "severity": t.severity, "status": t.status.value,
        # PII (technician_name, phone, email) intentionally excluded.
    } for t, d in rows])


@router.get("/dataset/ai-predictions", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT", "ADMIN"))])
def dataset_ai_predictions(db: Session = Depends(get_db)):
    rows = db.query(AIAnalysisResult).all()
    return success([{
        "ticket_id": r.ticket_id, "model_name": r.model_name, "model_version": r.model_version,
        "predicted_failure_mode": r.predicted_failure_mode, "predicted_component": r.predicted_component,
        "predicted_department": r.predicted_department, "confidence": r.confidence,
        "prediction_timestamp": r.prediction_timestamp,
    } for r in rows])


@router.get("/dataset/predictive-maintenance", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT", "ADMIN"))])
def dataset_predictive(db: Session = Depends(get_db)):
    devices = {d.id: d.device_id for d in db.query(Device).all()}
    health = db.query(DeviceHealth).all()
    anomalies = db.query(Anomaly).all()
    preventive = db.query(PreventiveTicket).all()
    predictions = db.query(PredictiveEvent).all()
    return success({
        "device_health": [{"device_id": devices.get(h.device_id), "health_score": h.health_score,
                            "anomaly_score": h.anomaly_score, "status": h.status,
                            "timestamp": h.timestamp} for h in health],
        "anomalies": [{"device_id": devices.get(a.device_id), "anomaly_score": a.anomaly_score,
                        "detected_at": a.detected_at, "resolved": a.resolved} for a in anomalies],
        "preventive_tickets": [{"device_id": devices.get(p.device_id), "status": p.status,
                                 "created_at": p.created_at} for p in preventive],
        "predictive_events": [{"device_id": devices.get(p.device_id), "predicted_issue": p.predicted_issue,
                                "confidence": p.confidence, "risk_level": p.risk_level,
                                "actual_outcome": p.actual_outcome, "timestamp": p.timestamp}
                               for p in predictions],
    })
