from app.schemas.chatbot import ChatRequest, ChatResponse
from app.services.gemini_service import gemini_service
from app.utils.responses import success
from app.auth.deps import require_roles
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/chat", tags=["Gemini Chatbot"])


@router.post("/message", dependencies=[Depends(require_roles("TECHNICIAN"))])
def chat_message(payload: ChatRequest):
    """
    Frontend -> FastAPI -> Gemini -> FastAPI -> Frontend.
    The Gemini API key never reaches the browser; the backend also enforces
    role (TECHNICIAN only, per current requirements) before forwarding.
    """
    reply = gemini_service.send_message(
        payload.message,
        context={"device_id": payload.device_id, "ticket_id": payload.ticket_id},
    )
    return success(ChatResponse(reply=reply).model_dump())
