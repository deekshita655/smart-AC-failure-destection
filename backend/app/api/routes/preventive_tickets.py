from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.predictive import PreventiveTicket
from app.models.device import Device
from app.models.enums import PreventiveTicketStatus
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles, get_current_user

router = APIRouter(prefix="/preventive-tickets", tags=["Preventive Tickets"])


@router.get("", dependencies=[Depends(require_roles("OVERALL_MANAGEMENT", "TECHNICIAN"))])
def list_preventive_tickets(db: Session = Depends(get_db)):
    rows = db.query(PreventiveTicket).order_by(PreventiveTicket.created_at.desc()).all()
    devices = {d.id: d.device_id for d in db.query(Device).all()}
    return success([{
        "id": p.id, "device_id": devices.get(p.device_id), "status": p.status,
        "created_at": p.created_at, "linked_service_ticket_id": p.linked_service_ticket_id,
    } for p in rows])


@router.post("/{preventive_ticket_id}/acknowledge", dependencies=[Depends(require_roles(
    "TECHNICIAN", "OVERALL_MANAGEMENT"))])
def acknowledge(preventive_ticket_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    pt = db.query(PreventiveTicket).get(preventive_ticket_id)
    if not pt:
        raise_error("RESOURCE_NOT_FOUND", "Preventive ticket not found.")
    pt.status = PreventiveTicketStatus.ACKNOWLEDGED.value
    pt.acknowledged_by = user.id
    pt.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    return success({"id": pt.id, "status": pt.status})


@router.post("/{preventive_ticket_id}/link-service-ticket", dependencies=[Depends(require_roles("TECHNICIAN"))])
def link_service_ticket(preventive_ticket_id: int, service_ticket_db_id: int, db: Session = Depends(get_db)):
    """
    Lets the preventive ticket enter the existing technician/service-note
    workflow: once the technician creates a normal ServiceTicket to act on it,
    this links the two records for traceability and closes the preventive ticket.
    """
    pt = db.query(PreventiveTicket).get(preventive_ticket_id)
    if not pt:
        raise_error("RESOURCE_NOT_FOUND", "Preventive ticket not found.")
    pt.linked_service_ticket_id = service_ticket_db_id
    pt.status = PreventiveTicketStatus.LINKED_TO_SERVICE.value
    db.commit()
    return success({"id": pt.id, "status": pt.status, "linked_service_ticket_id": pt.linked_service_ticket_id})
