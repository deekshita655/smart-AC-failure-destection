"""
StorageService - swappable file storage abstraction. MVP implementation stores
files on local disk under settings.LOCAL_UPLOAD_DIR. The route/service layer
only ever calls this interface, so the implementation can be swapped for
Azure Blob Storage (or any object store) later WITHOUT changing the API
contract (the API still returns a `file_path` key, whose meaning is
"a storage key", not a literal OS path).
"""
import os
import uuid
from app.core.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = settings.MAX_UPLOAD_MB * 1024 * 1024


class StorageService:
    def __init__(self):
        os.makedirs(settings.LOCAL_UPLOAD_DIR, exist_ok=True)

    def validate(self, content_type: str, size_bytes: int):
        from app.utils.responses import raise_error
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise_error("FILE_UPLOAD_ERROR", f"Unsupported file type: {content_type}")
        if size_bytes > MAX_BYTES:
            raise_error("FILE_UPLOAD_ERROR", f"File exceeds max size of {settings.MAX_UPLOAD_MB}MB")

    def save(self, ticket_id: str, filename: str, content: bytes) -> str:
        key = f"{ticket_id}/{uuid.uuid4().hex}_{filename}"
        full_path = os.path.join(settings.LOCAL_UPLOAD_DIR, key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(content)
        return key  # storage key, returned to caller as file_path


storage_service = StorageService()
