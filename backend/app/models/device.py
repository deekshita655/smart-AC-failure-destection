from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin


class Device(Base, TimestampMixin):
    """
    A physical Smart AC unit. Non-PII, safe for analytics/ML joins.
    """
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, nullable=False, index=True)
    product_model = Column(String(64), nullable=False, index=True)
    serial_range = Column(String(64), nullable=False, index=True)
    manufacturing_date = Column(DateTime, nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False)

    service_tickets = relationship("ServiceTicket", back_populates="device")
    sensor_readings = relationship("SensorReading", back_populates="device")
    health_records = relationship("DeviceHealth", back_populates="device")
    anomalies = relationship("Anomaly", back_populates="device")
    predictive_events = relationship("PredictiveEvent", back_populates="device")
