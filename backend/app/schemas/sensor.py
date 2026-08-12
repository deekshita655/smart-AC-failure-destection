from datetime import datetime
from pydantic import BaseModel


class SensorReadingIn(BaseModel):
    device_id: str
    timestamp: datetime
    temperature: float | None = None
    compressor_current: float | None = None
    vibration: float | None = None
    fan_speed: float | None = None
    power_consumption: float | None = None
    refrigerant_pressure: float | None = None
    humidity: float | None = None


class DeviceHealthResponse(BaseModel):
    device_id: str
    timestamp: datetime
    health_score: float
    anomaly_score: float
    status: str

    class Config:
        from_attributes = True


class PreventiveTicketResponse(BaseModel):
    id: int
    device_id: str
    status: str
    created_at: datetime
    linked_service_ticket_id: int | None = None

    class Config:
        from_attributes = True
