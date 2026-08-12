from fastapi import Depends, Header
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.utils.responses import raise_error


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise_error("AUTH_TOKEN_INVALID", "Missing or malformed Authorization header.")

    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise_error("AUTH_TOKEN_INVALID", "Session invalid or expired. Please log in again.")

    if payload.get("type") != "access":
        raise_error("AUTH_TOKEN_INVALID", "Refresh token cannot be used for API access.")

    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user or not user.is_active:
        raise_error("AUTH_TOKEN_INVALID", "User account not found or inactive.")
    return user


def require_roles(*roles: str):
    """
    Server-side RBAC enforcement dependency. Frontend button-hiding is NOT
    sufficient; every protected route must depend on this.
    """
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in roles and user.role.value != "ADMIN":
            raise_error("FORBIDDEN_ROLE", f"Role '{user.role.value}' is not permitted to access this resource.")
        return user
    return _checker
