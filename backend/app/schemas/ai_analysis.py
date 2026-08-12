from datetime import datetime
from typing import Any
from pydantic import BaseModel


class AIAnalysisRequest(BaseModel):
    """Fields explicitly excluded: failure_mode/component/department ground-truth labels
    are NEVER sent to the model as inputs - only these fields are."""
    record: str
    date: datetime
    product_model: str
    serial_range: str
    fix_text: str | None = None
    symptom_text: str
    ocr_text: str | None = None


class AIAnalysisResponse(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}
    model_name: str
    model_version: str
    prediction_timestamp: datetime
    predicted_failure_mode: str | None
    predicted_component: str | None
    predicted_department: str | None
    confidence: float | None
    suggested_action: str | None
    low_confidence: bool = False


class ComparisonResponse(BaseModel):
    failure_mode_match: bool | None = None
    component_match: bool | None = None
    department_match: bool | None = None
    overall_match: bool | None = None


class MLRawPayload(BaseModel):
    """
    Envelope accepted from the ML team. Schema is NOT frozen - everything beyond
    the currently-known fields is preserved in `extra` and passed through the
    ml_adapter untouched, so a schema change does not break this endpoint.
    """
    model_config = {"protected_namespaces": ()}
    model_name: str | None = None
    model_version: str | None = None
    failure_mode: str | None = None
    component: str | None = None
    department: str | None = None
    confidence: float | None = None
    suggested_action: str | None = None
    extra: dict[str, Any] | None = None
