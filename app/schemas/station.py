from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class StationCreate(BaseModel):
    code: str
    name: str
    city: str
    state: str

    @field_validator("code")
    @classmethod
    def code_uppercase(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Station code cannot be blank")
        return v.strip().upper()

    @field_validator("name", "city", "state")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be blank")
        return v.strip()


class StationUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    is_active: Optional[bool] = None


class StationResponse(BaseModel):
    id: int
    code: str
    name: str
    city: str
    state: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
