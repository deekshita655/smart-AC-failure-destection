from datetime import timedelta
from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from sqlalchemy import func,case
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.auth.deps import require_roles
from app.utils.responses import success
router=APIRouter(prefix="/analytics",tags=["Role-Specific Analytics"])
def _window(db,q,col,days=7):
 latest=db.query(func.max(col)).scalar()
 if latest is None:return []
 end=latest.date(); start=end-timedelta(days=days-1); rows=q.filter(col>=start,col<end+timedelta(days=1)).group_by(func.date(col)).order_by(func.date(col)).all(); c={str(d):int(n) for d,n in rows}; return [{"date":str(start+timedelta(days=i)),"count":c.get(str(start+timedelta(days=i)),0)} for i in range(days)]
@router.get("/quality/fix-history",dependencies=[Depends(require_roles("QUALITY"))])
def fix_history(db:Session=Depends(get_db)):
 fixes=db.query(ServiceTicket.fix_text,func.count()).filter(ServiceTicket.fix_text.isnot(None)).group_by(ServiceTicket.fix_text).order_by(func.count().desc()).limit(20).all(); comps=db.query(ServiceTicket.technician_diagnosis_component,func.count()).filter(ServiceTicket.fix_text.isnot(None)).group_by(ServiceTicket.technician_diagnosis_component).order_by(func.count().desc()).limit(20).all(); sev=db.query(ServiceTicket.severity,func.count()).group_by(ServiceTicket.severity).all(); q=db.query(func.date(ServiceTicket.date),func.count(ServiceTicket.id)).filter(ServiceTicket.fix_text.isnot(None)); return success({"most_common_fixes":[{"fix_text":f,"count":n} for f,n in fixes],"components_requiring_frequent_repair":[{"component":c or "DIAGNOSIS PENDING","count":n} for c,n in comps],"severity_distribution":[{"severity":s or "UNSPECIFIED","count":n} for s,n in sev],"repair_trend":_window(db,q,ServiceTicket.date)})
@router.get("/design/failure-trends",dependencies=[Depends(require_roles("DESIGN"))])
def failure_trends(db:Session=Depends(get_db)):
 fm=case((ServiceTicket.ground_truth_failure_mode.isnot(None),ServiceTicket.ground_truth_failure_mode),(ServiceTicket.technician_diagnosis_failure_mode.isnot(None),ServiceTicket.technician_diagnosis_failure_mode),else_="DIAGNOSIS PENDING"); comp=case((ServiceTicket.ground_truth_component.isnot(None),ServiceTicket.ground_truth_component),(ServiceTicket.technician_diagnosis_component.isnot(None),ServiceTicket.technician_diagnosis_component),else_="DIAGNOSIS PENDING")
 mm=db.query(Device.product_model,fm,func.count()).join(ServiceTicket,ServiceTicket.device_id==Device.id).group_by(Device.product_model,fm).all(); byc=db.query(comp,func.count()).group_by(comp).order_by(func.count().desc()).all(); byf=db.query(fm,func.count()).group_by(fm).order_by(func.count().desc()).all(); q=db.query(func.date(ServiceTicket.date),func.count(ServiceTicket.id)); models=db.query(Device.product_model,func.count(ServiceTicket.id)).join(ServiceTicket,ServiceTicket.device_id==Device.id).group_by(Device.product_model).order_by(func.count().desc()).all(); return success({"model_x_failure_mode_matrix":[{"product_model":m,"failure_mode":f,"count":n} for m,f,n in mm],"component_trends":[{"component":c,"count":n} for c,n in byc],"failure_mode_distribution":[{"failure_mode":f,"count":n} for f,n in byf],"failure_trend":_window(db,q,ServiceTicket.date),"model_distribution":[{"product_model":m,"count":n} for m,n in models]})
