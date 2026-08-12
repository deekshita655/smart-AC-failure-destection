from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.core.security import hash_password
from app.models.enums import RoleEnum
from pydantic import BaseModel
from app.utils.responses import success, raise_error
from app.auth.deps import require_roles

router = APIRouter(prefix="/users", tags=["Users / RBAC"])


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: RoleEnum
    technician_name: str | None = None
    phone_number: str | None = None
    email: str | None = None


@router.post("", dependencies=[Depends(require_roles("ADMIN"))])
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise_error("DUPLICATE_RESOURCE", "Username already exists.")
    user = User(
        username=payload.username, hashed_password=hash_password(payload.password),
        role=payload.role, technician_name=payload.technician_name,
        phone_number=payload.phone_number, email=payload.email,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success({"id": user.id, "username": user.username, "role": user.role.value}, status_code=201)


@router.get("", dependencies=[Depends(require_roles("ADMIN"))])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return success([{"id": u.id, "username": u.username, "role": u.role.value,
                      "is_active": u.is_active} for u in users])
