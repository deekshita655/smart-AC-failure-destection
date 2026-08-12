from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.service_ticket import ServiceTicket
from app.services.embedding_service import embedding_service
from app.services.azure_openai_service import azure_openai_service
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles

router = APIRouter(prefix="/service-tickets", tags=["Embeddings / Clustering"])


@router.post("/{ticket_id}/embed", dependencies=[Depends(require_roles("ADMIN"))])
def embed_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """
    Generates an embedding for a ticket's sanitized symptom text. The vector
    itself is never returned to the caller - only a confirmation - since
    embeddings are internal-only and feed the clustering pipeline (app/ml).
    """
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")

    sanitized = azure_openai_service._sanitize(ticket.symptom_text)
    _vector = embedding_service.embed(sanitized)  # not persisted/returned in MVP; clustering runs offline via app/ml
    return success({"ticket_id": ticket_id, "embedded": True, "vector_length": len(_vector)})
