from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


class PassengerInput(BaseModel):
    name: str
    age: int
    gender: str

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        allowed = {"MALE", "FEMALE", "OTHER"}
        if v.upper() not in allowed:
            raise ValueError(f"gender must be one of: {allowed}")
        return v.upper()

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v <= 0 or v > 120:
            raise ValueError("age must be between 1 and 120")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Passenger name cannot be blank")
        return v.strip()


class BookingCreate(BaseModel):
    train_id: int
    train_class_id: int
    source_station_id: int
    destination_station_id: int
    journey_date: str
    passengers: List[PassengerInput]

    @field_validator("journey_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        from datetime import date
        try:
            d = date.fromisoformat(v)
        except ValueError:
            raise ValueError("journey_date must be in YYYY-MM-DD format")
        if d < date.today():
            raise ValueError("journey_date cannot be in the past")
        return v

    @field_validator("passengers")
    @classmethod
    def validate_passengers(cls, v: list) -> list:
        if not v:
            raise ValueError("At least one passenger is required")
        if len(v) > 6:
            raise ValueError("Maximum 6 passengers per booking")
        return v


class PassengerResponse(BaseModel):
    id: int
    name: str
    age: int
    gender: str
    seat_number: Optional[str]

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    transaction_id: str
    amount: float
    payment_method: str
    payment_status: str
    note: str

    model_config = {"from_attributes": True}


class BookingResponse(BaseModel):
    id: int
    pnr: str
    train_number: str
    train_name: str
    source_station: str
    destination_station: str
    journey_date: str
    class_code: str
    total_fare: float
    seats_booked: int
    status: str
    passengers: List[PassengerResponse]
    payment: Optional[PaymentResponse]
    booked_at: datetime
    cancelled_at: Optional[datetime]

    model_config = {"from_attributes": True}


class CancelBookingResponse(BaseModel):
    pnr: str
    status: str
    refund_amount: float
    message: str
