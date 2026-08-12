from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    device_id: str | None = None
    ticket_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
