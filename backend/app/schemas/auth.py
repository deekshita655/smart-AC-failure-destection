from pydantic import BaseModel, Field
from app.models.enums import RoleEnum


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: int
    username: str
    role: RoleEnum
    technician_name: str | None = None
