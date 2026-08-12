from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.models.ai_analysis_result import AIAnalysisResult
from app.schemas.ai_analysis import ComparisonResponse
from app.utils.responses import success, raise_error
from app.auth.deps import get_current_user

router = APIRouter(prefix="/service-tickets", tags=["Technician vs AI Comparison"])


@router.get("/{ticket_id}/comparison")
def compare_ticket(ticket_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")

    latest_ai = (db.query(AIAnalysisResult)
                 .filter(AIAnalysisResult.ticket_id == ticket.id)
                 .order_by(AIAnalysisResult.id.desc()).first())

    if not latest_ai or not ticket.technician_diagnosis_failure_mode:
        # Technician diagnosis is optional - only compare fields that are present.
        return success(ComparisonResponse().model_dump())

    fm_match = ticket.technician_diagnosis_failure_mode == latest_ai.predicted_failure_mode
    comp_match = ticket.technician_diagnosis_component == latest_ai.predicted_component
    dept_match = ticket.technician_diagnosis_department == latest_ai.predicted_department

    return success(ComparisonResponse(
        failure_mode_match=fm_match, component_match=comp_match,
        department_match=dept_match, overall_match=fm_match and comp_match and dept_match,
    ).model_dump())
