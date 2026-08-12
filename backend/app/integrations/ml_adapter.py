"""
ml_adapter - translates whatever JSON the ML team eventually supplies into the
canonical AIAnalysisResult shape. This is the ONLY place that should need to
change when the ML team's schema evolves; everything downstream (DB, API
responses, comparison logic) depends on the canonical shape, not the raw ML JSON.

Currently known ML output shape (not frozen):
{
  "failure_mode": "...", "component": "...", "department": "...",
  "confidence": 0.91, "suggested_action": "...",
  "model_name": "...", "model_version": "..."
}
"""
from datetime import datetime, timezone


def normalize_ml_output(raw: dict) -> dict:
    return {
        "model_name": raw.get("model_name") or "unnamed-ml-model",
        "model_version": raw.get("model_version") or "unversioned",
        "prediction_timestamp": datetime.now(timezone.utc),
        "predicted_failure_mode": raw.get("failure_mode"),
        "predicted_component": raw.get("component"),
        "predicted_department": raw.get("department"),
        "confidence": raw.get("confidence"),
        "suggested_action": raw.get("suggested_action"),
        "raw_result_json": raw,
        "normalized_result_json": {
            "failure_mode": raw.get("failure_mode"),
            "component": raw.get("component"),
            "department": raw.get("department"),
            "confidence": raw.get("confidence"),
            "suggested_action": raw.get("suggested_action"),
        },
    }
