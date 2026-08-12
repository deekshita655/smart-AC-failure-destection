from datetime import datetime
from pydantic import BaseModel, Field


class DeviceLookupRequest(BaseModel):
    identifier: str
    identifier_type: str = Field(default="device_id", description="device_id | barcode | qr")


class DeviceResponse(BaseModel):
    device_id: str
    product_model: str
    serial_range: str
    manufacturing_date: datetime | None = None
    status: str

    class Config:
        from_attributes = True


class DeviceCreateRequest(BaseModel):
    device_id: str
    product_model: str
    serial_range: str
    manufacturing_date: datetime | None = None
