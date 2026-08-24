"""Create deterministic, non-PII analytics demo data. Run from backend: python seed_analytics_demo.py."""
from datetime import datetime,timedelta
from app.core.database import Base,SessionLocal,engine
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.device import Device
from app.models.predictive import Anomaly,DeviceHealth,PreventiveTicket,PredictiveEvent
from app.models.service_ticket import ServiceTicket
from app.models.user import User
from app.models.enums import TicketStatus
import app.models
Base.metadata.create_all(bind=engine); db=SessionLocal()
try:
 tech=db.query(User).filter(User.username=="tech1").first()
 if not tech: raise RuntimeError("Run python seed.py first so tech1 exists.")
 specs=[("DEMO-AN-001","AC-Model-X1","SR-001"),("DEMO-AN-002","AC-Model-X1","SR-001"),("DEMO-AN-003","AC-Model-X2","SR-002"),("DEMO-AN-004","AC-Model-X2","SR-002"),("DEMO-AN-005","AC-Model-Z2","SR-007"),("DEMO-AN-006","AC-Model-Z2","SR-008")]; devices={}
 for did,model,serial in specs:
  d=db.query(Device).filter(Device.device_id==did).first()
  if not d:d=Device(device_id=did,product_model=model,serial_range=serial,manufacturing_date=datetime(2023,1,1),status="ACTIVE");db.add(d);db.flush()
  devices[did]=d
 anchor=(db.query(ServiceTicket).order_by(ServiceTicket.date.desc()).first().date if db.query(ServiceTicket).first() else datetime.now()).replace(hour=15,minute=0,second=0,microsecond=0)
 tickets=[("Compressor failure","Compressor","Refrigeration","CRITICAL","Replaced compressor"),("Refrigerant leak","Refrigerant circuit","Refrigeration","MAJOR","Sealed leak and recharged refrigerant"),("Fan motor fault","Fan motor","Mechanical","MAJOR","Replaced fan motor"),("Electrical fault","PCB","Electrical","CRITICAL","Replaced control PCB"),("Sensor drift","Temperature sensor","Controls","MINOR","Calibrated sensor"),("Compressor overload","Compressor","Refrigeration","MAJOR","Adjusted compressor and cleaned coil")]*3
 created=0
 for i,(mode,comp,dept,sev,fix) in enumerate(tickets,1):
  tid=f"DEMO-AN-{i:03d}"
  if db.query(ServiceTicket).filter(ServiceTicket.ticket_id==tid).first():continue
  did=list(devices)[(i-1)%6]; symptom={"Compressor failure":"AC not cooling; compressor cycles repeatedly","Refrigerant leak":"Cooling weak and refrigerant pressure low","Fan motor fault":"Indoor fan vibration and airflow reduced","Electrical fault":"Outdoor unit trips intermittently","Sensor drift":"Thermostat reading drifts from ambient","Compressor overload":"High compressor current and heat"}[mode]
  d=anchor-timedelta(days=14-(i%15)); t=ServiceTicket(ticket_id=tid,device_id=devices[did].id,technician_id=tech.id,date=d,symptom_text=symptom,fix_text=fix,technician_diagnosis_failure_mode=mode,technician_diagnosis_component=comp,technician_diagnosis_department=dept,severity=sev,ground_truth_failure_mode=mode,ground_truth_component=comp,ground_truth_department=dept,status=TicketStatus.COMPLETED);db.add(t);db.flush();db.add(AIAnalysisResult(ticket_id=t.id,model_name="smart-ac-demo-classifier",model_version="demo-v1",prediction_timestamp=d+timedelta(minutes=5),predicted_failure_mode=mode,predicted_component=comp,predicted_department=dept,confidence=min(.78+(i%5)*.04,.96),suggested_action=fix,raw_result_json={"demo":True},normalized_result_json={"failure_mode":mode,"component":comp,"department":dept}));created+=1
 db.commit()
 health=[58,76,69,42,91,63]; anomaly=[.72,.44,.55,.88,.18,.61]; status=["AT_RISK","HEALTHY","AT_RISK","CRITICAL","HEALTHY","AT_RISK"]
 for i,did in enumerate(devices):
  d=devices[did]
  if not db.query(DeviceHealth).filter(DeviceHealth.device_id==d.id,DeviceHealth.timestamp==anchor).first():db.add(DeviceHealth(device_id=d.id,timestamp=anchor,health_score=health[i],anomaly_score=anomaly[i],status=status[i]))
  issue=["Compressor degradation","Refrigerant pressure drift","Fan vibration","PCB instability","Sensor drift","Compressor overload"][i];risk=["HIGH","MEDIUM","MEDIUM","CRITICAL","LOW","HIGH"][i];outcome=["CONFIRMED","PENDING","FALSE_POSITIVE","CONFIRMED","PENDING","CONFIRMED"][i];ev=PredictiveEvent(device_id=d.id,timestamp=anchor,predicted_issue=issue,confidence=.73+.04*i,risk_level=risk,actual_outcome=outcome);db.add(ev);db.flush();db.add(Anomaly(device_id=d.id,detected_at=anchor,anomaly_score=anomaly[i],description=issue,resolved=outcome=="FALSE_POSITIVE"));
  if outcome in ("CONFIRMED","PENDING"):db.add(PreventiveTicket(device_id=d.id,predictive_event_id=ev.id,status="PENDING" if outcome=="PENDING" else "OPEN",created_at=anchor+timedelta(minutes=15)))
 db.commit();print(f"Analytics demo seed complete: {created} new tickets.")
finally:db.close()
