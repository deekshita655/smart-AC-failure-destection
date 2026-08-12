from fastapi import APIRouter
from app.utils.responses import success

router = APIRouter(tags=["Health / System Status"])


@router.get("/health")
def health():
    return success({"status": "ok"})
