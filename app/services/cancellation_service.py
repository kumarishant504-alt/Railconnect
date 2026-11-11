from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.booking import Booking
from app.models.train import SeatInventory
from app.models.payment import Payment
from app.models.user import User
from app.schemas.booking import CancelBookingResponse

REFUND_PERCENTAGE = 0.80


def cancel_booking(pnr: str, user: User, session: Session) -> CancelBookingResponse:
    booking = session.exec(select(Booking).where(Booking.pnr == pnr)).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role != "admin" and booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only cancel your own bookings")
    if booking.status == "CANCELLED":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="This booking is already cancelled")

    booking.status = "CANCELLED"
    booking.cancelled_at = datetime.now(timezone.utc)
    session.add(booking)

    inv = session.exec(select(SeatInventory).where(
        SeatInventory.train_id == booking.train_id,
        SeatInventory.train_class_id == booking.train_class_id,
        SeatInventory.journey_date == booking.journey_date,
    )).first()
    if inv:
        inv.booked_seats = max(0, inv.booked_seats - booking.seats_booked)
        inv.available_seats = inv.total_seats - inv.booked_seats
        session.add(inv)

    refund = round(booking.total_fare * REFUND_PERCENTAGE, 2)
    pay = session.exec(select(Payment).where(Payment.booking_id == booking.id)).first()
    if pay:
        pay.payment_status = "REFUNDED"
        pay.refunded_at = datetime.now(timezone.utc)
        pay.refund_amount = refund
        pay.note = (f"SIMULATED REFUND — {int(REFUND_PERCENTAGE*100)}% of "
                    f"Rs.{booking.total_fare}. No real money involved.")
        session.add(pay)

    session.commit()
    return CancelBookingResponse(
        pnr=pnr, status="CANCELLED", refund_amount=refund,
        message=(f"Booking cancelled. SIMULATED refund of Rs.{refund} "
                 f"({int(REFUND_PERCENTAGE*100)}%) initiated. "
                 "NOTE: This is a SIMULATED transaction — no real money is involved."),
    )
