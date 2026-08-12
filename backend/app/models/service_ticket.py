from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, UpdatedTimestampMixin
from app.models.enums import TicketStatus


class ServiceTicket(Base, TimestampMixin, UpdatedTimestampMixin):
    """
    Central failure record. Distinguishes:
      - RAW TECHNICIAN DATA   -> symptom_text, fix_text, technician_diagnosis_*
      - AI PREDICTION         -> stored separately in AIAnalysisResult
      - GROUND TRUTH          -> ground_truth_* (only set on confirmed repair/QA review)
    Raw technician data and ground truth are NEVER overwritten by AI predictions.
    """
    __tablename__ = "service_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(64), unique=True, nullable=False, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    date = Column(DateTime, nullable=False)

    # --- RAW TECHNICIAN DATA ---
    symptom_text = Column(Text, nullable=False)
    fix_text = Column(Text, nullable=True)
    technician_diagnosis_failure_mode = Column(String(128), nullable=True)
    technician_diagnosis_component = Column(String(128), nullable=True)
    technician_diagnosis_department = Column(String(64), nullable=True)
    severity = Column(String(32), nullable=True)

    # --- GROUND TRUTH (set only after confirmed repair / QA review) ---
    ground_truth_failure_mode = Column(String(128), nullable=True)
    ground_truth_component = Column(String(128), nullable=True)
    ground_truth_department = Column(String(64), nullable=True)

    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)

    device = relationship("Device", back_populates="service_tickets")
    technician = relationship("User", back_populates="service_tickets")
    images = relationship("ServiceTicketImage", back_populates="ticket")
    ai_results = relationship("AIAnalysisResult", back_populates="ticket")
