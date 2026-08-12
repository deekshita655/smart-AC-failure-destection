from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, MeResponse
from app.utils.responses import success, raise_error
from app.auth.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise_error("AUTH_INVALID_CREDENTIALS", "Invalid username or password.")
    if not user.is_active:
        raise_error("AUTH_INVALID_CREDENTIALS", "Account is inactive.")

    access = create_access_token(user.username, user.role.value)
    refresh = create_refresh_token(user.username, user.role.value)
    return success(TokenResponse(access_token=access, refresh_token=refresh).model_dump())


@router.post("/refresh")
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    data = decode_token(payload.refresh_token)
    if not data or data.get("type") != "refresh":
        raise_error("AUTH_TOKEN_INVALID", "Invalid refresh token.")
    user = db.query(User).filter(User.username == data.get("sub")).first()
    if not user or not user.is_active:
        raise_error("AUTH_TOKEN_INVALID", "User not found or inactive.")
    access = create_access_token(user.username, user.role.value)
    new_refresh = create_refresh_token(user.username, user.role.value)
    return success(TokenResponse(access_token=access, refresh_token=new_refresh).model_dump())


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return success(MeResponse(
        id=user.id, username=user.username, role=user.role, technician_name=user.technician_name
    ).model_dump())


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # Stateless JWT: logout is enforced client-side (token discard). Documented
    # limitation - see OPEN CONTRACTS in architecture.md re: token blacklisting.
    return success({"message": "Logged out. Discard tokens client-side."})
