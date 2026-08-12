from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service_ticket_image import ServiceTicketImage
from app.schemas.ocr import OCRSubmission
from app.integrations.ocr_adapter import normalize_ocr_output
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles

router = APIRouter(prefix="/images", tags=["OCR Integration"])


@router.post("/{image_id}/ocr", dependencies=[Depends(require_roles("TECHNICIAN", "ADMIN"))])
def submit_ocr(image_id: int, payload: OCRSubmission, db: Session = Depends(get_db)):
    """
    Receives OCR JSON from the analytics/OCR component (owned by that team) and
    attaches normalized text to the target image. Backend does not perform OCR.
    """
    image = db.query(ServiceTicketImage).get(image_id)
    if not image:
        raise_error("RESOURCE_NOT_FOUND", "Image not found.")

    raw = payload.model_dump()
    if not raw.get("text"):
        raise_error("INVALID_OCR_PAYLOAD", "OCR payload missing required 'text' field.")

    normalized = normalize_ocr_output(raw)
    image.ocr_text = normalized["text"]
    image.ocr_raw_json = normalized["raw_json"]
    image.ocr_submitted_at = datetime.now(timezone.utc)
    db.commit()
    return success({"image_id": image_id, "ocr_text": image.ocr_text})
