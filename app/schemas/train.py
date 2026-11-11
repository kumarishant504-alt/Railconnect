from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class TrainCreate(BaseModel):
    train_number: str
    name: str
    train_type: str = "EXPRESS"

    @field_validator("train_number")
    @classmethod
    def validate_number(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Train number cannot be blank")
        return v.strip().upper()

    @field_validator("train_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"EXPRESS", "SUPERFAST", "LOCAL", "RAJDHANI", "SHATABDI", "DURONTO"}
        if v.upper() not in allowed:
            raise ValueError(f"train_type must be one of: {allowed}")
        return v.upper()


class TrainUpdate(BaseModel):
    name: Optional[str] = None
    train_type: Optional[str] = None
    is_active: Optional[bool] = None


class TrainStopCreate(BaseModel):
    station_id: int
    stop_order: int
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None
    day_offset: int = 0

    @field_validator("arrival_time", "departure_time")
    @classmethod
    def validate_time(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM format")
        h, m = v.split(":")
        if not (0 <= int(h) <= 23 and 0 <= int(m) <= 59):
            raise ValueError("Invalid time value")
        return v


class TrainStopResponse(BaseModel):
    id: int
    train_id: int
    station_id: int
    stop_order: int
    arrival_time: Optional[str]
    departure_time: Optional[str]
    day_offset: int
    station_code: Optional[str] = None
    station_name: Optional[str] = None
    city: Optional[str] = None

    model_config = {"from_attributes": True}


class TrainClassCreate(BaseModel):
    class_code: str
    class_name: str
    total_seats: int
    fare_per_km: float

    @field_validator("class_code")
    @classmethod
    def validate_class_code(cls, v: str) -> str:
        allowed = {"SL", "3A", "2A", "1A", "CC", "EC", "GN"}
        if v.upper() not in allowed:
            raise ValueError(f"class_code must be one of: {allowed}")
        return v.upper()

    @field_validator("total_seats")
    @classmethod
    def validate_seats(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("total_seats must be greater than 0")
        return v

    @field_validator("fare_per_km")
    @classmethod
    def validate_fare(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("fare_per_km must be greater than 0")
        return v


class TrainClassResponse(BaseModel):
    id: int
    train_id: int
    class_code: str
    class_name: str
    total_seats: int
    fare_per_km: float

    model_config = {"from_attributes": True}


class TrainResponse(BaseModel):
    id: int
    train_number: str
    name: str
    train_type: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TrainDetailResponse(BaseModel):
    id: int
    train_number: str
    name: str
    train_type: str
    is_active: bool
    stops: List[TrainStopResponse] = []
    classes: List[TrainClassResponse] = []

    model_config = {"from_attributes": True}


class TrainSearchResult(BaseModel):
    train_id: int
    train_number: str
    train_name: str
    train_type: str
    source_station: str
    source_city: str
    departure_time: str
    destination_station: str
    destination_city: str
    arrival_time: str
    journey_date: str
    available_classes: List[dict]
