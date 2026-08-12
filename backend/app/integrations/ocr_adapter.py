"""
ocr_adapter - translates the analytics/OCR team's JSON into the canonical
{text, raw_json} shape stored on ServiceTicketImage. Additional OCR metadata
(bounding boxes, per-line confidence, etc.) is preserved verbatim in raw_json
even though it is not yet used, so nothing is lost when the OCR schema evolves.
"""


def normalize_ocr_output(raw: dict) -> dict:
    text = raw.get("text") or raw.get("full_text") or raw.get("ocr_text") or ""
    return {"text": text, "raw_json": raw}
