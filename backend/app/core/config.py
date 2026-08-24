"""
Centralized application configuration.
All secrets/config MUST come from environment variables. Never hardcode secrets.
Values marked CONFIGURATION_PENDING in .env.example must be supplied by the
respective owning team (Azure team, Gemini integration owner, DevOps) before
those integrations will function. The app still boots without them; only the
specific integration call fails gracefully with AI_SERVICE_UNAVAILABLE /
CHATBOT_SERVICE_UNAVAILABLE.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "CONFIGURATION_PENDING_change_me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = "postgresql+psycopg2://ac_user:ac_password@localhost:5432/smart_ac_db"

    AZURE_OPENAI_ENDPOINT: str = "CONFIGURATION_PENDING"
    AZURE_OPENAI_API_KEY: str = "CONFIGURATION_PENDING"
    AZURE_OPENAI_API_VERSION: str = "CONFIGURATION_PENDING"
    AZURE_OPENAI_DEPLOYMENT: str = "CONFIGURATION_PENDING"

    AZURE_OPENAI_EMBEDDING_ENDPOINT: str = "CONFIGURATION_PENDING"
    AZURE_OPENAI_EMBEDDING_API_KEY: str = "CONFIGURATION_PENDING"
    AZURE_OPENAI_EMBEDDING_API_VERSION: str = "CONFIGURATION_PENDING"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "CONFIGURATION_PENDING"

    GEMINI_API_KEY: str = "CONFIGURATION_PENDING"
    GEMINI_API_URL: str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    AI_MIN_CONFIDENCE: float = 0.55
    PREDICTIVE_HEALTH_THRESHOLD: float = 40.0
    PREDICTIVE_ANOMALY_THRESHOLD: float = 0.7

    LOCAL_UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 8

    # ML failure-theme mining (from supplied ML pipeline).
    # Disabled auto-loading keeps existing backend startup behavior unchanged;
    # the model is loaded only when an ML endpoint is called or when an artifact
    # is explicitly enabled through ML_AUTO_LOAD.
    ML_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    ML_N_CLUSTERS: int = 5
    ML_ARTIFACT_DIR: str = "ml_artifacts"
    ML_AUTO_LOAD: bool = False


settings = Settings()
