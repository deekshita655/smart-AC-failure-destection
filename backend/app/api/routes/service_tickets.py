from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.models.enums import TicketStatus
from app.schemas.service_ticket import ServiceTicketCreateRequest, ServiceTicketResponse, GroundTruthUpdateRequest
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles, get_current_user

router = APIRouter(prefix="/service-tickets", tags=["Technician Service Tickets"])


@router.post("", dependencies=[Depends(require_roles("TECHNICIAN"))])
def create_ticket(payload: ServiceTicketCreateRequest, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", "Cannot create a ticket for an unknown device.")

    existing = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == payload.ticket_id).first()
    if existing:
        raise_error("DUPLICATE_RESOURCE", "ticket_id already exists.")

    ticket = ServiceTicket(
        ticket_id=payload.ticket_id,
        device_id=device.id,
        technician_id=user.id,
        date=payload.date,
        symptom_text=payload.symptom_text,
        fix_text=payload.fix_text,
        technician_diagnosis_failure_mode=payload.technician_diagnosis_failure_mode,
        technician_diagnosis_component=payload.technician_diagnosis_component,
        technician_diagnosis_department=payload.technician_diagnosis_department,
        severity=payload.severity,
        status=TicketStatus.OPEN,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return success(_ticket_response(ticket, device.device_id), status_code=201)


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")
    device = db.query(Device).get(ticket.device_id)
    return success(_ticket_response(ticket, device.device_id))


@router.post("/{ticket_id}/complete", dependencies=[Depends(require_roles("TECHNICIAN", "QUALITY"))])
def complete_ticket(ticket_id: str, payload: GroundTruthUpdateRequest, db: Session = Depends(get_db)):
    """
    Confirms the repair and records GROUND TRUTH. This never overwrites raw
    technician data or AI predictions - it is a distinct, explicit field set.
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")

    ticket.ground_truth_failure_mode = payload.ground_truth_failure_mode
    ticket.ground_truth_component = payload.ground_truth_component
    ticket.ground_truth_department = payload.ground_truth_department
    ticket.status = TicketStatus.COMPLETED
    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)
    device = db.query(Device).get(ticket.device_id)
    return success(_ticket_response(ticket, device.device_id))


def _ticket_response(ticket: ServiceTicket, device_id: str) -> dict:
    data = ServiceTicketResponse(
        ticket_id=ticket.ticket_id, device_id=device_id, date=ticket.date,
        symptom_text=ticket.symptom_text, fix_text=ticket.fix_text,
        technician_diagnosis_failure_mode=ticket.technician_diagnosis_failure_mode,
        technician_diagnosis_component=ticket.technician_diagnosis_component,
        technician_diagnosis_department=ticket.technician_diagnosis_department,
        severity=ticket.severity, status=ticket.status.value,
    ).model_dump()
    data["ground_truth"] = {
        "failure_mode": ticket.ground_truth_failure_mode,
        "component": ticket.ground_truth_component,
        "department": ticket.ground_truth_department,
    }
    return data
