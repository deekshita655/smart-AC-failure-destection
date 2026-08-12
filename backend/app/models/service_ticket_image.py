from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class ServiceTicketImage(Base, TimestampMixin):
    """
    Metadata for images uploaded against a service ticket, plus any OCR output
    later submitted by the analytics/OCR team for that image.
    File bytes are stored via the swappable StorageService (local disk in MVP).
    """
    __tablename__ = "service_ticket_images"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("service_tickets.id"), nullable=False, index=True)

    file_path = Column(String(512), nullable=False)   # storage-abstraction key, not a raw OS path contract
    file_name = Column(String(256), nullable=False)
    content_type = Column(String(64), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)

    # OCR (owned by analytics/OCR team - schema may evolve, kept as raw JSON + normalized text)
    ocr_text = Column(Text, nullable=True)
    ocr_raw_json = Column(JSON, nullable=True)
    ocr_submitted_at = Column(DateTime, nullable=True)

    ticket = relationship("ServiceTicket", back_populates="images")
