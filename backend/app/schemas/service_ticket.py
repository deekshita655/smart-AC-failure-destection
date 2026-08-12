from datetime import datetime
from pydantic import BaseModel


class ServiceTicketCreateRequest(BaseModel):
    """Technician-submitted RAW data. AI predictions are never written here."""
    ticket_id: str
    device_id: str
    date: datetime
    symptom_text: str
    fix_text: str | None = None
    technician_diagnosis_failure_mode: str | None = None
    technician_diagnosis_component: str | None = None
    technician_diagnosis_department: str | None = None
    severity: str | None = None


class ServiceTicketResponse(BaseModel):
    ticket_id: str
    device_id: str
    date: datetime
    symptom_text: str
    fix_text: str | None
    technician_diagnosis_failure_mode: str | None
    technician_diagnosis_component: str | None
    technician_diagnosis_department: str | None
    severity: str | None
    status: str

    class Config:
        from_attributes = True


class GroundTruthUpdateRequest(BaseModel):
    """Only settable via explicit confirm/complete-repair action, by TECHNICIAN or QUALITY."""
    ground_truth_failure_mode: str
    ground_truth_component: str
    ground_truth_department: str
