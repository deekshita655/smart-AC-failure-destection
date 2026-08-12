from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import RoleEnum


class User(Base, TimestampMixin):
    """
    Identity table. Contains PII (name, phone, email).
    PII fields must NEVER be forwarded to ML inputs or Power BI analytical datasets;
    downstream analytics should join on user_id only where absolutely required and
    prefer excluding this table entirely from analytical exports.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.TECHNICIAN)

    # PII - exclude from analytics/ML
    technician_name = Column(String(128), nullable=True)
    phone_number = Column(String(32), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)

    service_tickets = relationship("ServiceTicket", back_populates="technician")
