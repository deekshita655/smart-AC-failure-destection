from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.auth.deps import require_roles
from app.utils.responses import success

router = APIRouter(prefix="/analytics", tags=["Role-Specific Analytics"])


def _windowed_daily_counts(db, query, date_column, days=7):
    latest = db.query(func.max(date_column)).scalar()
    if latest is None:
        return []
    end_date = latest.date()
    start_date = end_date - timedelta(days=days - 1)
    rows = query.filter(date_column >= start_date, date_column < end_date + timedelta(days=1)) \
        .group_by(func.date(date_column)).order_by(func.date(date_column)).all()
    counts = {str(d): int(n) for d, n in rows}
    return [{"date": str(start_date + timedelta(days=i)), "count": counts.get(str(start_date + timedelta(days=i)), 0)} for i in range(days)]


@router.get("/quality/fix-history", dependencies=[Depends(require_roles("QUALITY"))])
def fix_history(db: Session = Depends(get_db)):
    common_fixes = (db.query(ServiceTicket.fix_text, func.count()).filter(ServiceTicket.fix_text.isnot(None))
                    .group_by(ServiceTicket.fix_text).order_by(func.count().desc()).limit(20).all())
    component_repairs = (db.query(ServiceTicket.technician_diagnosis_component, func.count())
                         .filter(ServiceTicket.fix_text.isnot(None))
                         .group_by(ServiceTicket.technician_diagnosis_component).order_by(func.count().desc()).limit(20).all())
    severity_dist = db.query(ServiceTicket.severity, func.count()).group_by(ServiceTicket.severity).all()
    repair_query = db.query(func.date(ServiceTicket.date).label("date"), func.count(ServiceTicket.id).label("count")) \
        .filter(ServiceTicket.fix_text.isnot(None))
    repair_trend = _windowed_daily_counts(db, repair_query, ServiceTicket.date)
    return success({
        "most_common_fixes": [{"fix_text": f, "count": n} for f, n in common_fixes],
        "components_requiring_frequent_repair": [{"component": c or "DIAGNOSIS PENDING", "count": n} for c, n in component_repairs],
        "severity_distribution": [{"severity": s or "UNSPECIFIED", "count": n} for s, n in severity_dist],
        "repair_trend": repair_trend,
    })


@router.get("/design/failure-trends", dependencies=[Depends(require_roles("DESIGN"))])
def failure_trends(db: Session = Depends(get_db)):
    failure_mode_expr = case(
        (ServiceTicket.ground_truth_failure_mode.isnot(None), ServiceTicket.ground_truth_failure_mode),
        (ServiceTicket.technician_diagnosis_failure_mode.isnot(None), ServiceTicket.technician_diagnosis_failure_mode),
        else_="DIAGNOSIS PENDING",
    )
    component_expr = case(
        (ServiceTicket.ground_truth_component.isnot(None), ServiceTicket.ground_truth_component),
        (ServiceTicket.technician_diagnosis_component.isnot(None), ServiceTicket.technician_diagnosis_component),
        else_="DIAGNOSIS PENDING",
    )
    by_model_failure = (db.query(Device.product_model, failure_mode_expr, func.count())
                        .join(ServiceTicket, ServiceTicket.device_id == Device.id)
                        .group_by(Device.product_model, failure_mode_expr).all())
    by_component = (db.query(component_expr, func.count())
                    .group_by(component_expr).order_by(func.count().desc()).all())
    by_failure_mode = (db.query(failure_mode_expr, func.count())
                       .group_by(failure_mode_expr).order_by(func.count().desc()).all())
    trend_query = db.query(func.date(ServiceTicket.date).label("date"), func.count(ServiceTicket.id).label("count"))
    failure_trend = _windowed_daily_counts(db, trend_query, ServiceTicket.date)
    model_distribution = (db.query(Device.product_model, func.count(ServiceTicket.id).label("count"))
                          .join(ServiceTicket, ServiceTicket.device_id == Device.id)
                          .group_by(Device.product_model).order_by(func.count().desc()).all())
    return success({
        "model_x_failure_mode_matrix": [{"product_model": m, "failure_mode": f, "count": n} for m, f, n in by_model_failure],
        "component_trends": [{"component": c, "count": n} for c, n in by_component],
        "failure_mode_distribution": [{"failure_mode": f, "count": n} for f, n in by_failure_mode],
        "failure_trend": failure_trend,
        "model_distribution": [{"product_model": m, "count": n} for m, n in model_distribution],
    })
