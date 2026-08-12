from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.service_ticket_image import ServiceTicketImage
from app.services.storage_service import storage_service
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles, get_current_user

router = APIRouter(prefix="/service-tickets", tags=["Images"])


@router.post("/{ticket_id}/images", dependencies=[Depends(require_roles("TECHNICIAN"))])
async def upload_image(ticket_id: str, file: UploadFile = File(...),
                        db: Session = Depends(get_db), user=Depends(get_current_user)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")
    if ticket.technician_id != user.id:
        raise_error("FORBIDDEN_ROLE", "You can only upload images to your own tickets.")

    content = await file.read()
    storage_service.validate(file.content_type, len(content))
    key = storage_service.save(ticket_id, file.filename, content)

    image = ServiceTicketImage(
        ticket_id=ticket.id, file_path=key, file_name=file.filename,
        content_type=file.content_type, file_size_bytes=len(content),
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return success({
        "image_id": image.id, "ticket_id": ticket_id, "file_name": image.file_name,
        "content_type": image.content_type, "file_size_bytes": image.file_size_bytes,
    }, status_code=201)


@router.get("/{ticket_id}/images")
def list_images(ticket_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")
    images = db.query(ServiceTicketImage).filter(ServiceTicketImage.ticket_id == ticket.id).all()
    return success([{
        "image_id": i.id, "file_name": i.file_name, "content_type": i.content_type,
        "file_size_bytes": i.file_size_bytes, "has_ocr": i.ocr_text is not None,
    } for i in images])
