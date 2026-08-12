from collections import Counter, defaultdict
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

# Answers analytics questions 1-11, 15-16 (see architecture.md PART 10).
# ALLOW: OVERALL_MANAGEMENT. QUALITY/DESIGN get scoped subsets via role_analytics.py.


def _month(value):
    """Return a stable YYYY-MM bucket for a datetime/date-like value."""
    return value.strftime("%Y-%m") if value else None


def _sorted_rows(counter):
    return [{"period": period, "count": count} for period, count in sorted(counter.items())]


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
        "model_x_ticket_count": [{"product_model": m, "ticket_count": n} for m, n in by_model],
        "department_distribution": [{"department": d or "UNKNOWN", "count": n} for d, n in by_department],
        "failure_mode_distribution": [{"failure_mode": f or "UNKNOWN", "count": n} for f, n in by_failure_mode],
        "avg_ai_confidence": float(avg_confidence) if avg_confidence else None,
        "predictive_maintenance": {
            "anomalies_detected": anomalies_count,
            "preventive_tickets_generated": preventive_count,
            "predicted_failures_confirmed": confirmed,
            "predictions_pending": pending,
            "false_positive_alerts": false_positive,
        },
    })


@router.get("/trends", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def analytics_trends(db: Session = Depends(get_db)):
    """Monthly, data-backed trends for management charts.

    Technician diagnosis remains separate from AI prediction/ground truth. Empty
    dimensions are represented as UNKNOWN instead of being silently discarded.
    """
    tickets = db.query(
        ServiceTicket.date,
        ServiceTicket.technician_diagnosis_failure_mode,
        ServiceTicket.technician_diagnosis_component,
    ).all()

    monthly = Counter()
    failure_modes = defaultdict(Counter)
    components = defaultdict(Counter)
    for date, failure_mode, component in tickets:
        period = _month(date)
        if not period:
            continue
        monthly[period] += 1
        failure_modes[period][failure_mode or "UNKNOWN"] += 1
        components[period][component or "UNKNOWN"] += 1

    prediction_events = db.query(
        PredictiveEvent.timestamp, PredictiveEvent.actual_outcome
    ).all()
    prediction_outcomes = defaultdict(Counter)
    for timestamp, outcome in prediction_events:
        period = _month(timestamp)
        if period:
            prediction_outcomes[period][outcome or "PENDING"] += 1

    return success({
        "failure_trends": _sorted_rows(monthly),
        "failure_mode_trends": [
            {"period": period, "failure_mode": mode, "count": count}
            for period in sorted(failure_modes)
            for mode, count in sorted(failure_modes[period].items())
        ],
        "component_trends": [
            {"period": period, "component": component, "count": count}
            for period in sorted(components)
            for component, count in sorted(components[period].items())
        ],
        "prediction_outcome_trends": [
            {"period": period, "outcome": outcome, "count": count}
            for period in sorted(prediction_outcomes)
            for outcome, count in sorted(prediction_outcomes[period].items())
        ],
    })


@router.get("/serial-range-analysis", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT", "DESIGN"))])
def serial_range_analysis(db: Session = Depends(get_db)):
    """
    Denominator = total tickets per serial_range; a serial range is flagged
    'investigate' when its ticket share materially exceeds its device-population
    share (simple MVP heuristic, not a statistical test).
    """
    rows = (db.query(Device.serial_range, func.count(ServiceTicket.id), func.count(func.distinct(Device.id)))
            .join(ServiceTicket, ServiceTicket.device_id == Device.id)
            .group_by(Device.serial_range).all())
    result = []
    for serial_range, ticket_count, device_count in rows:
        ratio = round(ticket_count / device_count, 2) if device_count else None
        result.append({
            "serial_range": serial_range, "ticket_count": ticket_count,
            "device_count": device_count, "tickets_per_device": ratio,
        })
    return success(sorted(result, key=lambda r: (r["tickets_per_device"] or 0), reverse=True))
