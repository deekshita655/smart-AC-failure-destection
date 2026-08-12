from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.utils.responses import success
from app.auth.deps import require_roles

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", dependencies=[Depends(require_roles("ADMIN"))])
def list_audit_logs(db: Session = Depends(get_db), limit: int = 100):
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return success([{
        "request_id": r.request_id, "user_id": r.user_id, "timestamp": r.timestamp,
        "action": r.action, "resource": r.resource, "result": r.result,
        "model_version": r.model_version, "ai_service_used": r.ai_service_used,
    } for r in rows])
