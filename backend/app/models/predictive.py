from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.enums import DeviceHealthStatus, PreventiveTicketStatus


class SensorReading(Base):
    """
    Simulated sensor stream sent directly from the Python simulator to FastAPI
    (no IoT Hub / Event Hub in MVP scope).
    """
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    temperature = Column(Float, nullable=True)
    compressor_current = Column(Float, nullable=True)
    vibration = Column(Float, nullable=True)
    fan_speed = Column(Float, nullable=True)
    power_consumption = Column(Float, nullable=True)
    refrigerant_pressure = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)

    device = relationship("Device", back_populates="sensor_readings")


class DeviceHealth(Base):
    __tablename__ = "device_health"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    health_score = Column(Float, nullable=False)     # 0-100, higher = healthier
    anomaly_score = Column(Float, nullable=False)     # 0-1, higher = more anomalous
    status = Column(String(32), default=DeviceHealthStatus.HEALTHY.value, nullable=False)

    device = relationship("Device", back_populates="health_records")


class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    detected_at = Column(DateTime, nullable=False, index=True)
    anomaly_score = Column(Float, nullable=False)
    description = Column(String(512), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)

    device = relationship("Device", back_populates="anomalies")


class PredictiveEvent(Base):
    __tablename__ = "predictive_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    predicted_issue = Column(String(256), nullable=True)
    confidence = Column(Float, nullable=True)
    risk_level = Column(String(32), nullable=True)  # LOW | MEDIUM | HIGH | CRITICAL
    actual_outcome = Column(String(64), nullable=True)  # CONFIRMED | FALSE_POSITIVE | PENDING

    device = relationship("Device", back_populates="predictive_events")


class PreventiveTicket(Base):
    __tablename__ = "preventive_tickets"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    predictive_event_id = Column(Integer, ForeignKey("predictive_events.id"), nullable=True)
    status = Column(String(32), default=PreventiveTicketStatus.PENDING.value, nullable=False)
    created_at = Column(DateTime, nullable=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    linked_service_ticket_id = Column(Integer, ForeignKey("service_tickets.id"), nullable=True)
