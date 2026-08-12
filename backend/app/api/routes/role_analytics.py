from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.auth.deps import require_roles
from app.utils.responses import success

router = APIRouter(prefix="/analytics", tags=["Role-Specific Analytics"])


@router.get("/quality/fix-history", dependencies=[Depends(require_roles("QUALITY"))])
def fix_history(db: Session = Depends(get_db)):
    common_fixes = (db.query(ServiceTicket.fix_text, func.count()).filter(ServiceTicket.fix_text.isnot(None))
                    .group_by(ServiceTicket.fix_text).order_by(func.count().desc()).limit(20).all())
    component_repairs = (db.query(ServiceTicket.technician_diagnosis_component, func.count())
                         .group_by(ServiceTicket.technician_diagnosis_component).order_by(func.count().desc()).limit(20).all())
    severity_dist = db.query(ServiceTicket.severity, func.count()).group_by(ServiceTicket.severity).all()
    repair_trend = (db.query(func.date(ServiceTicket.date).label("date"), func.count(ServiceTicket.id).label("count"))
                    .filter(ServiceTicket.fix_text.isnot(None)).group_by(func.date(ServiceTicket.date))
                    .order_by(func.date(ServiceTicket.date)).all())
    return success({
        "most_common_fixes": [{"fix_text": f, "count": n} for f, n in common_fixes],
        "components_requiring_frequent_repair": [{"component": c or "UNKNOWN", "count": n} for c, n in component_repairs],
        "severity_distribution": [{"severity": s or "UNKNOWN", "count": n} for s, n in severity_dist],
        "repair_trend": [{"date": str(d), "count": n} for d, n in repair_trend],
    })


@router.get("/design/failure-trends", dependencies=[Depends(require_roles("DESIGN"))])
def failure_trends(db: Session = Depends(get_db)):
    by_model_failure = (db.query(Device.product_model, ServiceTicket.technician_diagnosis_failure_mode, func.count())
                         .join(ServiceTicket, ServiceTicket.device_id == Device.id)
                         .group_by(Device.product_model, ServiceTicket.technician_diagnosis_failure_mode).all())
    by_component = (db.query(ServiceTicket.technician_diagnosis_component, func.count())
                    .group_by(ServiceTicket.technician_diagnosis_component).order_by(func.count().desc()).all())
    by_failure_mode = (db.query(ServiceTicket.technician_diagnosis_failure_mode, func.count())
                       .group_by(ServiceTicket.technician_diagnosis_failure_mode).order_by(func.count().desc()).all())
    failure_trend = (db.query(func.date(ServiceTicket.date).label("date"), func.count(ServiceTicket.id).label("count"))
                     .group_by(func.date(ServiceTicket.date)).order_by(func.date(ServiceTicket.date)).all())
    model_distribution = (db.query(Device.product_model, func.count(ServiceTicket.id).label("count"))
                          .join(ServiceTicket, ServiceTicket.device_id == Device.id)
                          .group_by(Device.product_model).order_by(func.count().desc()).all())
    return success({
        "model_x_failure_mode_matrix": [{"product_model": m, "failure_mode": f or "UNKNOWN", "count": n} for m, f, n in by_model_failure],
        "component_trends": [{"component": c or "UNKNOWN", "count": n} for c, n in by_component],
        "failure_mode_distribution": [{"failure_mode": f or "UNKNOWN", "count": n} for f, n in by_failure_mode],
        "failure_trend": [{"date": str(d), "count": n} for d, n in failure_trend],
        "model_distribution": [{"product_model": m or "UNKNOWN", "count": n} for m, n in model_distribution],
    })
