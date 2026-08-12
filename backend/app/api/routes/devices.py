from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.device import Device
from app.models.service_ticket import ServiceTicket
from app.schemas.device import DeviceLookupRequest, DeviceResponse, DeviceCreateRequest
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles, get_current_user

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.post("/lookup")
def lookup_device(payload: DeviceLookupRequest, db: Session = Depends(get_db),
                   user=Depends(get_current_user)):
    """
    Backend never scans a barcode itself - the frontend decodes it and sends the
    resulting identifier string here. identifier_type lets the frontend signal
    how the string was obtained without the backend assuming a single format.
    """
    device = db.query(Device).filter(Device.device_id == payload.identifier).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", f"No device found for identifier '{payload.identifier}'.")

    ticket_count = db.query(func.count(ServiceTicket.id)).filter(
        ServiceTicket.device_id == device.id
    ).scalar()

    return success({
        "device": DeviceResponse.model_validate(device).model_dump(),
        "summary": {"total_service_tickets": ticket_count},
    })


@router.post("", dependencies=[Depends(require_roles("ADMIN"))])
def create_device(payload: DeviceCreateRequest, db: Session = Depends(get_db)):
    existing = db.query(Device).filter(Device.device_id == payload.device_id).first()
    if existing:
        raise_error("DUPLICATE_RESOURCE", "Device with this device_id already exists.")
    device = Device(**payload.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return success(DeviceResponse.model_validate(device).model_dump(), status_code=201)


@router.get("/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        raise_error("DEVICE_NOT_FOUND", f"No device found for '{device_id}'.")
    return success(DeviceResponse.model_validate(device).model_dump())
