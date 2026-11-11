from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Station(SQLModel, table=True):
    __tablename__ = "stations"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True, max_length=10)
    name: str = Field(max_length=100)
    city: str = Field(max_length=100)
    state: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
