from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.predictive import DeviceHealth, Anomaly, PredictiveEvent, PreventiveTicket
from app.utils.responses import success
from app.auth.deps import require_roles

router = APIRouter(prefix="/analytics/manufacturer", tags=["Manufacturer Analytics"])


@router.get("/overview", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def overview(db: Session = Depends(get_db)):
    total_tickets = db.query(func.count(ServiceTicket.id)).scalar()
    total_devices = db.query(func.count(Device.id)).scalar()
    by_model = (db.query(Device.product_model, func.count(ServiceTicket.id))
                .join(ServiceTicket, ServiceTicket.device_id == Device.id)
                .group_by(Device.product_model).all())
    by_department = (db.query(ServiceTicket.technician_diagnosis_department, func.count())
                      .group_by(ServiceTicket.technician_diagnosis_department).all())
    by_failure_mode = (db.query(ServiceTicket.technician_diagnosis_failure_mode, func.count())
                        .group_by(ServiceTicket.technician_diagnosis_failure_mode).all())
    avg_confidence = db.query(func.avg(AIAnalysisResult.confidence)).scalar()
    anomalies_count = db.query(func.count(Anomaly.id)).scalar()
    preventive_count = db.query(func.count(PreventiveTicket.id)).scalar()
    confirmed = db.query(func.count(PredictiveEvent.id)).filter(PredictiveEvent.actual_outcome == "CONFIRMED").scalar()
    pending = db.query(func.count(PredictiveEvent.id)).filter(PredictiveEvent.actual_outcome == "PENDING").scalar()
    false_positive = db.query(func.count(PredictiveEvent.id)).filter(PredictiveEvent.actual_outcome == "FALSE_POSITIVE").scalar()
    return success({
        "total_service_tickets": total_tickets, "total_devices": total_devices,
        "model_x_ticket_count": [{"product_model": m, "ticket_count": n} for m, n in by_model],
        "department_distribution": [{"department": d or "UNKNOWN", "count": n} for d, n in by_department],
        "failure_mode_distribution": [{"failure_mode": f or "UNKNOWN", "count": n} for f, n in by_failure_mode],
        "avg_ai_confidence": float(avg_confidence) if avg_confidence else None,
        "predictive_maintenance": {"anomalies_detected": anomalies_count, "preventive_tickets_generated": preventive_count,
                                   "predicted_failures_confirmed": confirmed, "predictions_pending": pending,
                                   "false_positive_alerts": false_positive},
    })


@router.get("/failure-trend", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def failure_trend(db: Session = Depends(get_db)):
    rows = (db.query(func.date(ServiceTicket.date).label("date"), func.count(ServiceTicket.id).label("count"))
            .group_by(func.date(ServiceTicket.date)).order_by(func.date(ServiceTicket.date)).all())
    return success([{"date": str(d), "count": n} for d, n in rows])


@router.get("/serial-range-analysis", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT", "DESIGN"))])
def serial_range_analysis(db: Session = Depends(get_db)):
    rows = (db.query(Device.serial_range, func.count(ServiceTicket.id), func.count(func.distinct(Device.id)))
            .join(ServiceTicket, ServiceTicket.device_id == Device.id)
            .group_by(Device.serial_range).all())
    result = []
    for serial_range, ticket_count, device_count in rows:
        ratio = round(ticket_count / device_count, 2) if device_count else None
        result.append({"serial_range": serial_range, "ticket_count": ticket_count, "device_count": device_count, "tickets_per_device": ratio})
    return success(sorted(result, key=lambda r: (r["tickets_per_device"] or 0), reverse=True))
