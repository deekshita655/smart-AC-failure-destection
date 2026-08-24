from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, desc
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.predictive import DeviceHealth, Anomaly, PredictiveEvent, PreventiveTicket
from app.utils.responses import success
from app.auth.deps import require_roles

router = APIRouter(prefix="/analytics/manufacturer", tags=["Manufacturer Analytics"])


def _month_parts(column):
    return extract("year", column), extract("month", column)


def _period(year, month):
    return f"{int(year):04d}-{int(month):02d}"


# Answers analytics questions 1-11, 15-16 (see architecture.md PART 10).
# ALLOW: OVERALL_MANAGEMENT. QUALITY/DESIGN get scoped subsets via role_analytics.py.
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
    confirmed = db.query(func.count(PredictiveEvent.id)).filter(
        PredictiveEvent.actual_outcome == "CONFIRMED").scalar()
    pending = db.query(func.count(PredictiveEvent.id)).filter(
        PredictiveEvent.actual_outcome == "PENDING").scalar()
    false_positive = db.query(func.count(PredictiveEvent.id)).filter(
        PredictiveEvent.actual_outcome == "FALSE_POSITIVE").scalar()

    return success({
        "total_service_tickets": total_tickets,
        "total_devices": total_devices,
        "model_x_ticket_count": [{"product_model": m or "UNKNOWN", "ticket_count": n} for m, n in by_model],
        "department_distribution": [{"department": d or "UNKNOWN", "count": n} for d, n in by_department],
        "failure_mode_distribution": [{"failure_mode": f or "UNKNOWN", "count": n} for f, n in by_failure_mode],
        "avg_ai_confidence": float(avg_confidence) if avg_confidence is not None else None,
        "predictive_maintenance": {
            "anomalies_detected": anomalies_count,
            "preventive_tickets_generated": preventive_count,
            "predicted_failures_confirmed": confirmed,
            "predictions_pending": pending,
            "false_positive_alerts": false_positive,
        },
    })


@router.get("/trends", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def trends(db: Session = Depends(get_db)):
    """Monthly analytics derived from persisted timestamps; no synthetic history is created."""
    year, month = _month_parts(ServiceTicket.date)
    rows = (db.query(year.label("year"), month.label("month"), func.count(ServiceTicket.id))
            .group_by(year, month).order_by(year, month).all())
    failure_trends = [
        {"period": _period(y, m), "failure_count": n} for y, m, n in rows
    ]

    tech_year, tech_month = _month_parts(ServiceTicket.date)
    mode_rows = (db.query(tech_year.label("year"), tech_month.label("month"),
                          ServiceTicket.technician_diagnosis_failure_mode, func.count(ServiceTicket.id))
                 .filter(ServiceTicket.technician_diagnosis_failure_mode.isnot(None))
                 .group_by(tech_year, tech_month, ServiceTicket.technician_diagnosis_failure_mode)
                 .order_by(tech_year, tech_month).all())
    failure_mode_trends = [
        {"period": _period(y, m), "failure_mode": mode or "UNKNOWN", "count": n}
        for y, m, mode, n in mode_rows
    ]

    gt_year, gt_month = _month_parts(ServiceTicket.date)
    gt_rows = (db.query(gt_year.label("year"), gt_month.label("month"),
                       ServiceTicket.ground_truth_failure_mode, func.count(ServiceTicket.id))
               .filter(ServiceTicket.ground_truth_failure_mode.isnot(None))
               .group_by(gt_year, gt_month, ServiceTicket.ground_truth_failure_mode)
               .order_by(gt_year, gt_month).all())
    confirmed_failure_mode_trends = [
        {"period": _period(y, m), "failure_mode": mode or "UNKNOWN", "count": n}
        for y, m, mode, n in gt_rows
    ]

    comp_year, comp_month = _month_parts(ServiceTicket.date)
    component_rows = (db.query(comp_year.label("year"), comp_month.label("month"),
                               ServiceTicket.technician_diagnosis_component, func.count(ServiceTicket.id))
                      .filter(ServiceTicket.technician_diagnosis_component.isnot(None))
                      .group_by(comp_year, comp_month, ServiceTicket.technician_diagnosis_component)
                      .order_by(comp_year, comp_month).all())
    component_trends = [
        {"period": _period(y, m), "component": component or "UNKNOWN", "count": n}
        for y, m, component, n in component_rows
    ]

    device_year, device_month = _month_parts(ServiceTicket.date)
    device_rows = (db.query(device_year.label("year"), device_month.label("month"),
                            Device.device_id, func.count(ServiceTicket.id))
                   .join(Device, ServiceTicket.device_id == Device.id)
                   .group_by(device_year, device_month, Device.device_id)
                   .order_by(device_year, device_month).all())
    device_ticket_trends = [
        {"period": _period(y, m), "device_id": device_id, "ticket_count": n}
        for y, m, device_id, n in device_rows
    ]

    outcome_year, outcome_month = _month_parts(PredictiveEvent.timestamp)
    outcome_rows = (db.query(outcome_year.label("year"), outcome_month.label("month"),
                             PredictiveEvent.actual_outcome, func.count(PredictiveEvent.id))
                    .filter(PredictiveEvent.actual_outcome.isnot(None))
                    .group_by(outcome_year, outcome_month, PredictiveEvent.actual_outcome)
                    .order_by(outcome_year, outcome_month).all())
    prediction_outcome_trends = [
        {"period": _period(y, m), "outcome": outcome, "count": n}
        for y, m, outcome, n in outcome_rows
    ]

    return success({
        "failure_trends": failure_trends,
        "failure_mode_trends": failure_mode_trends,
        "confirmed_failure_mode_trends": confirmed_failure_mode_trends,
        "component_failure_trends": component_trends,
        "device_ticket_trends": device_ticket_trends,
        "prediction_outcome_trends": prediction_outcome_trends,
    })


@router.get("/serial-range-analysis", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT", "DESIGN"))])
def serial_range_analysis(db: Session = Depends(get_db)):
    rows = (db.query(Device.serial_range, func.count(ServiceTicket.id), func.count(func.distinct(Device.id)))
            .join(ServiceTicket, ServiceTicket.device_id == Device.id)
            .group_by(Device.serial_range).all())
    result = []
    for serial_range, ticket_count, device_count in rows:
        ratio = round(ticket_count / device_count, 2) if device_count else None
        result.append({
            "serial_range": serial_range or "UNKNOWN", "ticket_count": ticket_count,
            "device_count": device_count, "tickets_per_device": ratio,
        })
    return success(sorted(result, key=lambda r: (r["tickets_per_device"] or 0), reverse=True))
