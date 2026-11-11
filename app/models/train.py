from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Train(SQLModel, table=True):
    __tablename__ = "trains"

    id: Optional[int] = Field(default=None, primary_key=True)
    train_number: str = Field(unique=True, index=True, max_length=10)
    name: str = Field(max_length=150)
    train_type: str = Field(default="EXPRESS", max_length=30)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TrainStop(SQLModel, table=True):
    __tablename__ = "train_stops"

    id: Optional[int] = Field(default=None, primary_key=True)
    train_id: int = Field(foreign_key="trains.id", index=True)
    station_id: int = Field(foreign_key="stations.id")
    stop_order: int
    arrival_time: Optional[str] = Field(default=None, max_length=5)
    departure_time: Optional[str] = Field(default=None, max_length=5)
    day_offset: int = Field(default=0)


class TrainClass(SQLModel, table=True):
    __tablename__ = "train_classes"

    id: Optional[int] = Field(default=None, primary_key=True)
    train_id: int = Field(foreign_key="trains.id", index=True)
    class_code: str = Field(max_length=10)
    class_name: str = Field(max_length=50)
    total_seats: int
    fare_per_km: float


class SeatInventory(SQLModel, table=True):
    __tablename__ = "seat_inventory"

    id: Optional[int] = Field(default=None, primary_key=True)
    train_id: int = Field(foreign_key="trains.id", index=True)
    train_class_id: int = Field(foreign_key="train_classes.id", index=True)
    journey_date: str = Field(index=True)
    total_seats: int
    booked_seats: int = Field(default=0)
    available_seats: int
