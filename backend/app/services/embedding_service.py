"""
EmbeddingService - the ONLY place that talks to Azure OpenAI Embeddings.
Embedding vectors are internal-only and are never returned to normal frontend
users; they feed the Python clustering pipeline (see app/ml and app/analytics).

CONFIGURATION PENDING: AZURE_OPENAI_EMBEDDING_* env vars.
"""
import httpx
from app.core.config import settings
from app.utils.responses import raise_error

PENDING_VALUE = "CONFIGURATION_PENDING"


class EmbeddingService:
    def _configured(self) -> bool:
        return PENDING_VALUE not in (
            settings.AZURE_OPENAI_EMBEDDING_ENDPOINT,
            settings.AZURE_OPENAI_EMBEDDING_API_KEY,
            settings.AZURE_OPENAI_EMBEDDING_API_VERSION,
            settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        )

    def embed(self, sanitized_text: str) -> list[float]:
        if not self._configured():
            raise_error("CONFIGURATION_PENDING",
                        "Azure OpenAI Embeddings is not yet configured.")

        url = (f"{settings.AZURE_OPENAI_EMBEDDING_ENDPOINT}/openai/deployments/"
               f"{settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT}/embeddings"
               f"?api-version={settings.AZURE_OPENAI_EMBEDDING_API_VERSION}")
        headers = {"api-key": settings.AZURE_OPENAI_EMBEDDING_API_KEY, "Content-Type": "application/json"}
        try:
            with httpx.Client(timeout=20) as client:
                resp = client.post(url, headers=headers, json={"input": sanitized_text[:4000]})
                resp.raise_for_status()
                data = resp.json()
            return data["data"][0]["embedding"]
        except (httpx.HTTPError, KeyError, IndexError):
            raise_error("AI_SERVICE_UNAVAILABLE", "Embedding service is temporarily unavailable.")


embedding_service = EmbeddingService()
