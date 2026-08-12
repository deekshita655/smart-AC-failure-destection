"""
GeminiService - isolates the frontend chatbot from Gemini. The frontend only
ever calls POST /chat/message on our own backend; Gemini API keys never reach
the browser.
CONFIGURATION PENDING: GEMINI_API_KEY.
"""
import httpx
from app.core.config import settings
from app.utils.responses import raise_error

PENDING_VALUE = "CONFIGURATION_PENDING"


class GeminiService:
    def _configured(self) -> bool:
        return settings.GEMINI_API_KEY != PENDING_VALUE

    def send_message(self, message: str, context: dict | None = None) -> str:
        if not self._configured():
            raise_error("CHATBOT_SERVICE_UNAVAILABLE", "Chatbot is not yet configured.")

        context_str = ""
        if context:
            context_str = "Context: " + ", ".join(f"{k}={v}" for k, v in context.items() if v)

        payload = {
            "contents": [{"parts": [{"text": f"{context_str}\nTechnician question: {message}"}]}]
        }
        url = f"{settings.GEMINI_API_URL}?key={settings.GEMINI_API_KEY}"
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (httpx.HTTPError, KeyError, IndexError):
            raise_error("CHATBOT_SERVICE_UNAVAILABLE", "Chatbot is temporarily unavailable.")


gemini_service = GeminiService()
