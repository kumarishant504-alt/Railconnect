from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: Optional[int] = Field(default=None, primary_key=True)
    booking_id: int = Field(foreign_key="bookings.id", unique=True, index=True)
    amount: float
    payment_method: str = Field(default="MOCK_UPI", max_length=30)
    payment_status: str = Field(default="SUCCESS")
    transaction_id: str = Field(unique=True, max_length=50)
    paid_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    refunded_at: Optional[datetime] = Field(default=None)
    refund_amount: Optional[float] = Field(default=None)
    note: str = Field(default="SIMULATED PAYMENT — No real money involved", max_length=255)
