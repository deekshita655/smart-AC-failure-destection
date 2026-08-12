from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.core.database import Base


class AuditLog(Base):
    """
    Traceability for AI predictions, ticket lifecycle, preventive-ticket
    generation, technician-vs-AI mismatches, and role-sensitive analytics access.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    action = Column(String(128), nullable=False, index=True)
    resource = Column(String(128), nullable=True)
    result = Column(String(32), nullable=True)  # SUCCESS | FAILURE
    model_version = Column(String(64), nullable=True)
    ai_service_used = Column(String(64), nullable=True)
    extra = Column(JSON, nullable=True)
