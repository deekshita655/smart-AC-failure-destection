"""
Consistent API response envelope + centralized error taxonomy.
"""
import uuid
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def new_request_id() -> str:
    return str(uuid.uuid4())


def success(data, request_id: str | None = None, status_code: int = 200):
    payload = {"success": True, "data": data, "request_id": request_id or new_request_id()}
    return JSONResponse(status_code=status_code, content=jsonable_encoder(payload))


class APIError(Exception):
    """
    Raised anywhere in the app to produce a consistent, frontend-safe error body.
    Never carries stack traces, secrets, or DB connection details.
    """

    def __init__(self, code: str, message: str, status_code: int = 400,
                 retryable: bool = False, details=None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.details = details


# ---- Central error taxonomy -------------------------------------------------
# code                         -> (http_status, retryable)
ERROR_TAXONOMY = {
    "VALIDATION_ERROR":         (status.HTTP_422_UNPROCESSABLE_ENTITY, False),
    "AUTH_INVALID_CREDENTIALS": (status.HTTP_401_UNAUTHORIZED, False),
    "AUTH_TOKEN_EXPIRED":       (status.HTTP_401_UNAUTHORIZED, True),
    "AUTH_TOKEN_INVALID":       (status.HTTP_401_UNAUTHORIZED, False),
    "FORBIDDEN_ROLE":           (status.HTTP_403_FORBIDDEN, False),
    "DEVICE_NOT_FOUND":         (status.HTTP_404_NOT_FOUND, False),
    "TICKET_NOT_FOUND":         (status.HTTP_404_NOT_FOUND, False),
    "USER_NOT_FOUND":           (status.HTTP_404_NOT_FOUND, False),
    "RESOURCE_NOT_FOUND":       (status.HTTP_404_NOT_FOUND, False),
    "DUPLICATE_RESOURCE":       (status.HTTP_409_CONFLICT, False),
    "AI_SERVICE_UNAVAILABLE":   (status.HTTP_503_SERVICE_UNAVAILABLE, True),
    "AI_LOW_CONFIDENCE":        (status.HTTP_200_OK, False),
    "CHATBOT_SERVICE_UNAVAILABLE": (status.HTTP_503_SERVICE_UNAVAILABLE, True),
    "DATABASE_ERROR":           (status.HTTP_500_INTERNAL_SERVER_ERROR, True),
    "FILE_UPLOAD_ERROR":        (status.HTTP_400_BAD_REQUEST, False),
    "INVALID_OCR_PAYLOAD":      (status.HTTP_422_UNPROCESSABLE_ENTITY, False),
    "SENSOR_PAYLOAD_ERROR":     (status.HTTP_422_UNPROCESSABLE_ENTITY, False),
    "PREDICTION_ERROR":         (status.HTTP_500_INTERNAL_SERVER_ERROR, True),
    "CONFIGURATION_PENDING":    (status.HTTP_503_SERVICE_UNAVAILABLE, True),
}


def raise_error(code: str, message: str, details=None):
    http_status, retryable = ERROR_TAXONOMY.get(code, (400, False))
    raise APIError(code=code, message=message, status_code=http_status,
                    retryable=retryable, details=details)


def error_body(err: APIError, request_id: str):
    return {
        "success": False,
        "error": {
            "code": err.code,
            "message": err.message,
            "retryable": err.retryable,
            "details": err.details,
        },
        "request_id": request_id,
    }
