from typing import Any
from pydantic import BaseModel


class OCRSubmission(BaseModel):
    """
    Interface for the analytics/OCR team. Schema may evolve; unexpected keys are
    kept in raw_json and only `text` is required to plug into downstream AI analysis.
    """
    text: str
    raw_json: dict[str, Any] | None = None
