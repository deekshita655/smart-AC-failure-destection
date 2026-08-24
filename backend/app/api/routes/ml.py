from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.core.database import get_db
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.service_ticket import ServiceTicket
from app.services.ml_failure_mining_service import MLFailureMiningService
from app.utils.responses import raise_error, success

router = APIRouter(prefix="/ml", tags=["ML Failure Mining"])


def _service() -> MLFailureMiningService:
    return MLFailureMiningService()


@router.post("/train", dependencies=[Depends(require_roles("ADMIN"))])
def train_failure_mining(db: Session = Depends(get_db)):
    tickets = db.query(ServiceTicket).order_by(ServiceTicket.date.asc()).all()
    try:
        result = _service().train(tickets)
    except (ValueError, RuntimeError) as exc:
        raise_error("ML_TRAINING_FAILED", str(exc))
    return success(result, status_code=201)


@router.get("/status", dependencies=[Depends(require_roles("ADMIN", "OVERALL_MANAGEMENT"))])
def ml_status():
    service = _service()
    return success({"trained": service.is_fitted, "embedding_model": service.model_name,
                    "n_clusters": service.n_clusters, "artifact_dir": service.artifact_dir.as_posix()})


@router.post("/service-tickets/{ticket_id}/predict", dependencies=[Depends(require_roles("TECHNICIAN", "ADMIN"))])
def predict_ticket_cluster(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")
    try:
        prediction = _service().predict(ticket)
    except RuntimeError as exc:
        raise_error("ML_MODEL_NOT_TRAINED", str(exc))
    service = MLFailureMiningService()
    cluster = service.ensure_cluster_record(db, prediction["cluster_id"])
    db.commit()
    return success({"ticket_id": ticket.ticket_id, "model_name": prediction["model_name"],
                    "model_version": prediction["model_version"], "cluster_id": prediction["cluster_id"],
                    "cluster_record_id": cluster.id, "distance_to_centroid": prediction["distance_to_centroid"],
                    "cluster_profile": prediction["cluster_profile"]})


@router.post("/service-tickets/{ticket_id}/store-result", dependencies=[Depends(require_roles("TECHNICIAN", "ADMIN"))])
def store_ticket_cluster_result(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(ServiceTicket).filter(ServiceTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise_error("TICKET_NOT_FOUND", "Service ticket not found.")
    service = _service()
    try:
        prediction = service.predict(ticket)
    except RuntimeError as exc:
        raise_error("ML_MODEL_NOT_TRAINED", str(exc))
    cluster = service.ensure_cluster_record(db, prediction["cluster_id"])
    result = AIAnalysisResult(ticket_id=ticket.id, model_name=prediction["model_name"], model_version=prediction["model_version"],
        prediction_timestamp=datetime.now(timezone.utc), predicted_failure_mode=None, predicted_component=None,
        predicted_department=None, confidence=None, suggested_action=None, cluster_id=cluster.id,
        raw_result_json={"cluster_id": prediction["cluster_id"], "distance_to_centroid": prediction["distance_to_centroid"]},
        normalized_result_json={"cluster_id": prediction["cluster_id"], "distance_to_centroid": prediction["distance_to_centroid"]})
    db.add(result); db.commit(); db.refresh(result)
    return success({"ai_analysis_id": result.id, "ticket_id": ticket.ticket_id, "cluster_id": prediction["cluster_id"],
                    "cluster_record_id": cluster.id, "distance_to_centroid": prediction["distance_to_centroid"]}, status_code=201)
