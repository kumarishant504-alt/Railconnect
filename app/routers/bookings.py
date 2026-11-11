from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database.engine import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse, CancelBookingResponse
from app.services import booking_service, cancellation_service

router = APIRouter(prefix="/api/v1/bookings", tags=["Bookings"])


@router.post("/", response_model=BookingResponse, status_code=201)
def create_booking(data: BookingCreate, current_user: User = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    """Book a ticket. Fare is always calculated server-side."""
    return booking_service.create_booking(data, current_user, session)


@router.get("/my", response_model=List[BookingResponse])
def my_bookings(current_user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    """Get all bookings for the authenticated user."""
    return booking_service.get_user_bookings(current_user, session)


@router.get("/{pnr}", response_model=BookingResponse)
def get_booking(pnr: str, current_user: User = Depends(get_current_user),
                session: Session = Depends(get_session)):
    """Get booking by PNR. Passengers can only see their own bookings."""
    return booking_service.get_booking_by_pnr(pnr, current_user, session)


@router.post("/{pnr}/cancel", response_model=CancelBookingResponse)
def cancel_booking(pnr: str, current_user: User = Depends(get_current_user),
                   session: Session = Depends(get_session)):
    """Cancel a booking. Releases seats and creates a simulated refund."""
    return cancellation_service.cancel_booking(pnr, current_user, session)
