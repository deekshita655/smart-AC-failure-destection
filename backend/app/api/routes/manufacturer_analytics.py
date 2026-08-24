from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.predictive import Anomaly, PredictiveEvent, PreventiveTicket, DeviceHealth
from app.utils.responses import success
from app.auth.deps import require_roles
router=APIRouter(prefix="/analytics/manufacturer",tags=["Manufacturer Analytics"])
def _label(v,f="DIAGNOSIS PENDING"): return v or f
@router.get("/overview",dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def overview(db:Session=Depends(get_db)):
 total_tickets=db.query(func.count(ServiceTicket.id)).scalar() or 0; total_devices=db.query(func.count(Device.id)).scalar() or 0
 by_model=db.query(Device.product_model,func.count(ServiceTicket.id)).join(ServiceTicket,ServiceTicket.device_id==Device.id).group_by(Device.product_model).all()
 fm=case((ServiceTicket.ground_truth_failure_mode.isnot(None),ServiceTicket.ground_truth_failure_mode),(ServiceTicket.technician_diagnosis_failure_mode.isnot(None),ServiceTicket.technician_diagnosis_failure_mode),else_="DIAGNOSIS PENDING")
 comp=case((ServiceTicket.ground_truth_component.isnot(None),ServiceTicket.ground_truth_component),(ServiceTicket.technician_diagnosis_component.isnot(None),ServiceTicket.technician_diagnosis_component),else_="DIAGNOSIS PENDING")
 dept=case((ServiceTicket.ground_truth_department.isnot(None),ServiceTicket.ground_truth_department),(ServiceTicket.technician_diagnosis_department.isnot(None),ServiceTicket.technician_diagnosis_department),else_="DIAGNOSIS PENDING")
 by_department=db.query(dept,func.count()).group_by(dept).all(); by_failure_mode=db.query(fm,func.count()).group_by(fm).order_by(func.count().desc()).all(); by_component=db.query(comp,func.count()).group_by(comp).order_by(func.count().desc()).all(); severity=db.query(ServiceTicket.severity,func.count()).group_by(ServiceTicket.severity).order_by(func.count().desc()).all()
 avg_confidence=db.query(func.avg(AIAnalysisResult.confidence)).scalar(); anomalies_count=db.query(func.count(Anomaly.id)).scalar() or 0; preventive_count=db.query(func.count(PreventiveTicket.id)).scalar() or 0; confirmed=db.query(func.count(PredictiveEvent.id)).filter(PredictiveEvent.actual_outcome=="CONFIRMED").scalar() or 0; pending=db.query(func.count(PredictiveEvent.id)).filter(PredictiveEvent.actual_outcome=="PENDING").scalar() or 0; false_positive=db.query(func.count(PredictiveEvent.id)).filter(PredictiveEvent.actual_outcome=="FALSE_POSITIVE").scalar() or 0
 return success({"total_service_tickets":total_tickets,"total_devices":total_devices,"model_x_ticket_count":[{"product_model":_label(m,"UNKNOWN"),"ticket_count":n} for m,n in by_model],"department_distribution":[{"department":d,"count":n} for d,n in by_department],"failure_mode_distribution":[{"failure_mode":f,"count":n} for f,n in by_failure_mode],"component_distribution":[{"component":c,"count":n} for c,n in by_component],"severity_distribution":[{"severity":_label(s,"UNSPECIFIED"),"count":n} for s,n in severity],"avg_ai_confidence":float(avg_confidence) if avg_confidence is not None else None,"predictive_maintenance":{"anomalies_detected":anomalies_count,"preventive_tickets_generated":preventive_count,"predicted_failures_confirmed":confirmed,"predictions_pending":pending,"false_positive_alerts":false_positive}})
@router.get("/failure-trend",dependencies=[Depends(require_roles("OVERALL_MANAGEMENT"))])
def failure_trend(db:Session=Depends(get_db)):
 latest=db.query(func.max(ServiceTicket.date)).scalar()
 if latest is None:return success([])
 end=latest.date(); start=end-timedelta(days=6); rows=db.query(func.date(ServiceTicket.date).label("date"),func.count(ServiceTicket.id).label("count")).filter(ServiceTicket.date>=start,ServiceTicket.date<end+timedelta(days=1)).group_by(func.date(ServiceTicket.date)).all(); counts={str(d):int(n) for d,n in rows}
 return success([{"date":str(start+timedelta(days=i)),"count":counts.get(str(start+timedelta(days=i)),0)} for i in range(7)])
@router.get("/serial-range-analysis",dependencies=[Depends(require_roles("OVERALL_MANAGEMENT","DESIGN"))])
def serial_range_analysis(db:Session=Depends(get_db)):
 rows=db.query(Device.serial_range,func.count(ServiceTicket.id),func.count(func.distinct(Device.id))).join(ServiceTicket,ServiceTicket.device_id==Device.id).group_by(Device.serial_range).all(); result=[]
 for serial_range,ticket_count,device_count in rows: result.append({"serial_range":serial_range,"ticket_count":ticket_count,"device_count":device_count,"tickets_per_device":round(ticket_count/device_count,2) if device_count else None})
 return success(sorted(result,key=lambda r:(r["tickets_per_device"] or 0),reverse=True))
