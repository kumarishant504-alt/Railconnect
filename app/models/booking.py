from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Booking(SQLModel, table=True):
    __tablename__ = "bookings"

    id: Optional[int] = Field(default=None, primary_key=True)
    pnr: str = Field(unique=True, index=True, max_length=20)
    user_id: int = Field(foreign_key="users.id", index=True)
    train_id: int = Field(foreign_key="trains.id")
    train_class_id: int = Field(foreign_key="train_classes.id")
    source_station_id: int = Field(foreign_key="stations.id")
    destination_station_id: int = Field(foreign_key="stations.id")
    journey_date: str
    total_fare: float
    status: str = Field(default="CONFIRMED")
    seats_booked: int = Field(default=1)
    booked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cancelled_at: Optional[datetime] = Field(default=None)


class BookingPassenger(SQLModel, table=True):
    __tablename__ = "booking_passengers"

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id", index=True)
    name: str = Field(max_length=100)
    age: int
    gender: str = Field(max_length=10)
    seat_number: Optional[str] = Field(default=None, max_length=10)
