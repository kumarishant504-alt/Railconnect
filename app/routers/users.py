from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database.engine import get_session
from app.dependencies.auth import require_admin, get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/", response_model=List[UserResponse])
def list_users(session: Session = Depends(get_session), admin: User = Depends(require_admin)):
    """Admin only: list all users."""
    return list(session.exec(select(User)).all())


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: User = Depends(get_current_user),
             session: Session = Depends(get_session)):
    """Get user by ID. Passengers can only view their own profile."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
