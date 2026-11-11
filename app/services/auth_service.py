from datetime import datetime, timedelta, timezone
import secrets

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.user import User, PasswordResetToken
from app.schemas.user import UserRegister
from app.utils.security import hash_password, verify_password, create_access_token
from app.config import get_settings

settings = get_settings()


def register_user(data: UserRegister, session: Session) -> User:
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        phone=data.phone,
        role="passenger",
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(email: str, password: str, session: Session) -> User:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


def create_token_for_user(user: User) -> str:
    return create_access_token({"sub": str(user.id), "role": user.role})


def initiate_password_reset(email: str, session: Session) -> str:
    user = session.exec(select(User).where(User.email == email)).first()
    generic_msg = "If an account with this email exists, a reset link has been sent."
    if not user:
        return generic_msg

    old_tokens = session.exec(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False,
        )
    ).all()
    for t in old_tokens:
        t.used = True
        session.add(t)

    token_value = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.reset_token_expire_minutes)
    session.add(PasswordResetToken(user_id=user.id, token=token_value, expires_at=expires))
    session.commit()

    # Dev mode: print to console (replace with email in production)
    print(f"\n[DEV] Password reset token for {email}: {token_value}\n")
    return generic_msg


def reset_password(token_value: str, new_password: str, session: Session) -> str:
    token = session.exec(
        select(PasswordResetToken).where(PasswordResetToken.token == token_value)
    ).first()
    if not token or token.used:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    now = datetime.now(timezone.utc)
    expires = token.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires:
        raise HTTPException(status_code=400, detail="Reset token has expired")

    user = session.exec(select(User).where(User.id == token.user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_password)
    token.used = True
    session.add(user)
    session.add(token)
    session.commit()
    return "Password has been reset successfully"


def change_password(user: User, current_password: str, new_password: str, session: Session) -> str:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    session.add(user)
    session.commit()
    return "Password changed successfully"
