"""
Create deterministic, non-PII analytics demo data.

Run from backend:
    python seed_analytics_demo.py

This script is intentionally separate from seed.py. It only creates rows whose
IDs start with DEMO-AN- and is safe to run repeatedly.
"""
from datetime import datetime, timedelta

from app.core.database import Base, SessionLocal, engine
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.device import Device
from app.models.predictive import Anomaly, DeviceHealth, PreventiveTicket, PredictiveEvent
from app.models.service_ticket import ServiceTicket
from app.models.user import User
from app.models.enums import TicketStatus
import app.models  # noqa: F401

Base.metadata.create_all(bind=engine)
db = SessionLocal()

try:
    technician = db.query(User).filter(User.username == "tech1").first()
    if not technician:
        raise RuntimeError("Run `python seed.py` first so demo user tech1 exists.")

    devices_spec = [
        ("DEMO-AN-001", "AC-Model-X1", "SR-001"), ("DEMO-AN-002", "AC-Model-X1", "SR-001"),
        ("DEMO-AN-003", "AC-Model-X2", "SR-002"), ("DEMO-AN-004", "AC-Model-X2", "SR-002"),
        ("DEMO-AN-005", "AC-Model-Z2", "SR-007"), ("DEMO-AN-006", "AC-Model-Z2", "SR-008"),
    ]
    devices = {}
    for device_id, model, serial in devices_spec:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            device = Device(device_id=device_id, product_model=model, serial_range=serial,
                            manufacturing_date=datetime(2023, 1, 1), status="ACTIVE")
            db.add(device); db.flush()
        devices[device_id] = device

    latest_existing = db.query(ServiceTicket).order_by(ServiceTicket.date.desc()).first()
    anchor = (latest_existing.date if latest_existing else datetime.now()).replace(hour=15, minute=0, second=0, microsecond=0)
    ticket_specs = [
        (0,"DEMO-AN-001","AC not cooling; compressor cycles repeatedly","Compressor failure","Compressor","Refrigeration","CRITICAL","Replaced compressor"),
        (1,"DEMO-AN-002","Cooling weak and refrigerant pressure low","Refrigerant leak","Refrigerant circuit","Refrigeration","MAJOR","Sealed leak and recharged refrigerant"),
        (2,"DEMO-AN-003","Indoor fan vibration and airflow reduced","Fan motor fault","Fan motor","Mechanical","MAJOR","Replaced fan motor"),
        (3,"DEMO-AN-004","Outdoor unit trips intermittently","Electrical fault","PCB","Electrical","CRITICAL","Replaced control PCB"),
        (4,"DEMO-AN-005","Thermostat reading drifts from ambient","Sensor drift","Temperature sensor","Controls","MINOR","Calibrated sensor"),
        (5,"DEMO-AN-006","High compressor current and heat","Compressor overload","Compressor","Refrigeration","MAJOR","Adjusted compressor and cleaned coil"),
        (6,"DEMO-AN-001","Unit stops after startup","Electrical fault","PCB","Electrical","MAJOR","Replaced relay"),
        (7,"DEMO-AN-003","Low airflow with noisy fan","Fan motor fault","Fan motor","Mechanical","MINOR","Replaced fan bearing"),
        (8,"DEMO-AN-005","Cooling loss after several hours","Refrigerant leak","Refrigerant circuit","Refrigeration","MAJOR","Repaired joint and recharged"),
        (9,"DEMO-AN-002","Compressor starts but overheats","Compressor failure","Compressor","Refrigeration","CRITICAL","Replaced compressor"),
        (10,"DEMO-AN-004","Display error and control instability","Electrical fault","PCB","Electrical","MAJOR","Replaced PCB"),
        (11,"DEMO-AN-006","Temperature sensor reports unstable values","Sensor drift","Temperature sensor","Controls","MINOR","Replaced sensor"),
        (12,"DEMO-AN-003","Fan stalls intermittently","Fan motor fault","Fan motor","Mechanical","MAJOR","Replaced fan motor"),
        (13,"DEMO-AN-001","Compressor current above normal","Compressor overload","Compressor","Refrigeration","MAJOR","Cleaned condenser and adjusted charge"),
        (13,"DEMO-AN-004","Unit loses cooling with low pressure","Refrigerant leak","Refrigerant circuit","Refrigeration","MAJOR","Repaired leak"),
        (14,"DEMO-AN-005","Control panel intermittently resets","Electrical fault","PCB","Electrical","CRITICAL","Replaced PCB"),
        (14,"DEMO-AN-002","Weak cooling and high power draw","Compressor overload","Compressor","Refrigeration","MAJOR","Serviced compressor"),
        (14,"DEMO-AN-006","Fan vibration returns under load","Fan motor fault","Fan motor","Mechanical","MINOR","Replaced fan bearing"),
    ]
    prediction_map = {
        "Compressor failure": ("Compressor failure","Compressor","Refrigeration"),
        "Compressor overload": ("Compressor overload","Compressor","Refrigeration"),
        "Refrigerant leak": ("Refrigerant leak","Refrigerant circuit","Refrigeration"),
        "Fan motor fault": ("Fan motor fault","Fan motor","Mechanical"),
        "Electrical fault": ("Electrical fault","PCB","Electrical"),
        "Sensor drift": ("Sensor drift","Temperature sensor","Controls"),
    }
    created_tickets = 0
    for index, (days_ago, device_id, symptom, failure_mode, component, department, severity, fix) in enumerate(ticket_specs, 1):
        ticket_id = f"DEMO-AN-{index:03d}"
        if db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first(): continue
        ticket_date = anchor - timedelta(days=14 - days_ago)
        ticket = ServiceTicket(ticket_id=ticket_id, device_id=devices[device_id].id, technician_id=technician.id,
            date=ticket_date, symptom_text=symptom, fix_text=fix,
            technician_diagnosis_failure_mode=failure_mode, technician_diagnosis_component=component,
            technician_diagnosis_department=department, severity=severity,
            ground_truth_failure_mode=failure_mode, ground_truth_component=component,
            ground_truth_department=department, status=TicketStatus.COMPLETED)
        db.add(ticket); db.flush()
        predicted_mode, predicted_component, predicted_department = prediction_map[failure_mode]
        confidence = min(round(0.78 + (index % 5) * 0.04, 2), 0.96)
        db.add(AIAnalysisResult(ticket_id=ticket.id, model_name="smart-ac-demo-classifier", model_version="demo-v1",
            prediction_timestamp=ticket_date + timedelta(minutes=5), predicted_failure_mode=predicted_mode,
            predicted_component=predicted_component, predicted_department=predicted_department,
            confidence=confidence, suggested_action=fix, raw_result_json={"demo": True},
            normalized_result_json={"failure_mode":predicted_mode,"component":predicted_component,"department":predicted_department}))
        created_tickets += 1
    db.commit()

    health_specs = [
        ("DEMO-AN-001",58,0.72,"AT_RISK"),("DEMO-AN-002",76,0.44,"HEALTHY"),
        ("DEMO-AN-003",69,0.55,"AT_RISK"),("DEMO-AN-004",42,0.88,"CRITICAL"),
        ("DEMO-AN-005",91,0.18,"HEALTHY"),("DEMO-AN-006",63,0.61,"AT_RISK"),
    ]
    for device_id, health, anomaly, status in health_specs:
        device = devices[device_id]
        if not db.query(DeviceHealth).filter(DeviceHealth.device_id == device.id, DeviceHealth.timestamp == anchor).first():
            db.add(DeviceHealth(device_id=device.id, timestamp=anchor, health_score=health, anomaly_score=anomaly, status=status))

    base_scores = {"DEMO-AN-001":72,"DEMO-AN-002":82,"DEMO-AN-003":78,"DEMO-AN-004":64,"DEMO-AN-005":94,"DEMO-AN-006":75}
    for device_id, base in base_scores.items():
        device = devices[device_id]
        for offset in range(4, 0, -1):
            ts = anchor - timedelta(days=offset)
            if db.query(DeviceHealth).filter(DeviceHealth.device_id == device.id, DeviceHealth.timestamp == ts).first(): continue
            score = max(20, min(98, base - (4 - offset) * 3))
            db.add(DeviceHealth(device_id=device.id, timestamp=ts, health_score=score, anomaly_score=round(1-score/100,2),
                                 status="HEALTHY" if score >= 80 else "AT_RISK" if score >= 55 else "CRITICAL"))

    predictive_specs = [
        ("DEMO-AN-001","Compressor degradation",0.91,"HIGH","CONFIRMED"),("DEMO-AN-002","Refrigerant pressure drift",0.84,"MEDIUM","PENDING"),
        ("DEMO-AN-003","Fan vibration",0.73,"MEDIUM","FALSE_POSITIVE"),("DEMO-AN-004","PCB instability",0.94,"CRITICAL","CONFIRMED"),
        ("DEMO-AN-005","Sensor drift",0.82,"LOW","PENDING"),("DEMO-AN-006","Compressor overload",0.89,"HIGH","CONFIRMED"),
    ]
    health_by_device = {d:h for d,h,_,_ in health_specs}
    for device_id, issue, confidence, risk, outcome in predictive_specs:
        device = devices[device_id]
        event = db.query(PredictiveEvent).filter(PredictiveEvent.device_id == device.id, PredictiveEvent.timestamp == anchor).first()
        if not event:
            event = PredictiveEvent(device_id=device.id, timestamp=anchor, predicted_issue=issue, confidence=confidence,
                                    risk_level=risk, actual_outcome=outcome)
            db.add(event); db.flush()
        if outcome in ("CONFIRMED","PENDING") and not db.query(PreventiveTicket).filter(PreventiveTicket.predictive_event_id == event.id).first():
            db.add(PreventiveTicket(device_id=device.id, predictive_event_id=event.id,
                                     status="PENDING" if outcome == "PENDING" else "OPEN", created_at=anchor + timedelta(minutes=15)))
        if not db.query(Anomaly).filter(Anomaly.device_id == device.id, Anomaly.detected_at == anchor).first():
            db.add(Anomaly(device_id=device.id, detected_at=anchor, anomaly_score=round(1-health_by_device[device_id]/100,2),
                           description=issue, resolved=outcome == "FALSE_POSITIVE"))
    db.commit()
    print(f"Analytics demo seed complete: {created_tickets} new tickets.")
    print("Created/verified: 6 devices, AI predictions, health history, anomalies, predictive events and preventive tickets.")
finally:
    db.close()
