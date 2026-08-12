from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.service_ticket import ServiceTicket
from app.models.device import Device
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.enums import TicketStatus
from app.schemas.ai_analysis import MLRawPayload
from app.services.azure_openai_service import azure_openai_service
from app.integrations.ml_adapter import normalize_ml_output
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles

router = APIRouter(tags=["AI Analysis"])

# Design decision (see architecture.md PART 27): SYNCHRONOUS processing.
# Azure OpenAI chat-completion latency (~1-4s) is acceptable for a single
# technician submitting one ticket at a time; no job queue / worker needed
# for this MVP scale.


@router.post("/service-tickets/{ticket_id}/analyze", dependencies=[Depends(require_roles("TECHNICIAN"))])
def analyze_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")
    device = db.query(Device).get(ticket.device_id)

    result = azure_openai_service.classify_service_note(
        record=ticket.ticket_id,
        product_model=device.product_model,
        serial_range=device.serial_range,
        symptom_text=ticket.symptom_text,
        fix_text=ticket.fix_text,
        ocr_text=None,
    )

    ai_result = AIAnalysisResult(ticket_id=ticket.id, **result)
    db.add(ai_result)
    ticket.status = TicketStatus.ANALYZED
    db.commit()
    db.refresh(ai_result)

    low_confidence = (result.get("confidence") or 0) < settings.AI_MIN_CONFIDENCE
    return success({
        "model_name": ai_result.model_name, "model_version": ai_result.model_version,
        "prediction_timestamp": ai_result.prediction_timestamp,
        "predicted_failure_mode": ai_result.predicted_failure_mode,
        "predicted_component": ai_result.predicted_component,
        "predicted_department": ai_result.predicted_department,
        "confidence": ai_result.confidence,
        "suggested_action": ai_result.suggested_action,
        "low_confidence": low_confidence,
    })


@router.post("/service-tickets/{ticket_id}/ml-result", dependencies=[Depends(require_roles("ADMIN"))])
def submit_ml_result(ticket_id: str, payload: MLRawPayload, db: Session = Depends(get_db)):
    """
    Adapter entrypoint for the team's OWN ML pipeline (kmeans placeholder or
    future model) to push a prediction directly, bypassing Azure OpenAI.
    Whatever JSON shape the ML team lands on, only ml_adapter.py needs updating.
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")

    normalized = normalize_ml_output(payload.model_dump())
    ai_result = AIAnalysisResult(ticket_id=ticket.id, **normalized)
    db.add(ai_result)
    ticket.status = TicketStatus.ANALYZED
    db.commit()
    db.refresh(ai_result)
    return success({"ai_analysis_id": ai_result.id, "ticket_id": ticket_id}, status_code=201)


@router.get("/service-tickets/{ticket_id}/ai-results")
def get_ai_results(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")
    results = db.query(AIAnalysisResult).filter(AIAnalysisResult.ticket_id == ticket.id).all()
    return success([{
        "model_name": r.model_name, "model_version": r.model_version,
        "prediction_timestamp": r.prediction_timestamp,
        "predicted_failure_mode": r.predicted_failure_mode,
        "predicted_component": r.predicted_component,
        "predicted_department": r.predicted_department,
        "confidence": r.confidence, "suggested_action": r.suggested_action,
    } for r in results])
