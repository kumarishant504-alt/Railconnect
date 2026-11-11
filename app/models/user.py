from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str = Field(max_length=100)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str
    phone: Optional[str] = Field(default=None, max_length=15)
    role: str = Field(default="passenger")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PasswordResetToken(SQLModel, table=True):
    __tablename__ = "password_reset_tokens"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    token: str = Field(unique=True, index=True)
    expires_at: datetime
    used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
