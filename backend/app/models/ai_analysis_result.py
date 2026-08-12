from sqlalchemy import Column, Integer, String, ForeignKey, Float, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class AIAnalysisResult(Base, TimestampMixin):
    """
    Canonical AI PREDICTION record. This is what the ML team's evolving JSON
    schema is normalized into via app.integrations.ml_adapter, so downstream
    code never depends on the ML team's raw field names.
    """
    __tablename__ = "ai_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("service_tickets.id"), nullable=False, index=True)

    model_name = Column(String(128), nullable=False)
    model_version = Column(String(64), nullable=False)
    prediction_timestamp = Column(DateTime, nullable=False)

    predicted_failure_mode = Column(String(128), nullable=True)
    predicted_component = Column(String(128), nullable=True)
    predicted_department = Column(String(64), nullable=True)
    confidence = Column(Float, nullable=True)
    suggested_action = Column(Text, nullable=True)

    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)

    raw_result_json = Column(JSON, nullable=True)          # audit/debug only, never returned to normal users
    normalized_result_json = Column(JSON, nullable=True)   # canonical shape actually used by the app

    ticket = relationship("ServiceTicket", back_populates="ai_results")
    cluster = relationship("Cluster")
