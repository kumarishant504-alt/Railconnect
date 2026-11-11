from datetime import datetime, timezone
from typing import List
import uuid

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models.train import Train, TrainClass, TrainStop, SeatInventory
from app.models.station import Station
from app.models.booking import Booking, BookingPassenger
from app.models.payment import Payment
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse, PassengerResponse, PaymentResponse
from app.utils.pnr import generate_pnr


def _get_or_create_inventory(train_id, train_class_id, journey_date, total_seats, session):
    inv = session.exec(select(SeatInventory).where(
        SeatInventory.train_id == train_id,
        SeatInventory.train_class_id == train_class_id,
        SeatInventory.journey_date == journey_date,
    )).first()
    if not inv:
        inv = SeatInventory(train_id=train_id, train_class_id=train_class_id,
                            journey_date=journey_date, total_seats=total_seats,
                            booked_seats=0, available_seats=total_seats)
        session.add(inv)
        session.flush()
    return inv


def create_booking(data: BookingCreate, user: User, session: Session) -> BookingResponse:
    train = session.get(Train, data.train_id)
    if not train or not train.is_active:
        raise HTTPException(status_code=404, detail="Train not found or inactive")

    tc = session.exec(select(TrainClass).where(TrainClass.id == data.train_class_id,
                                                TrainClass.train_id == data.train_id)).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Train class not found for this train")

    src_stop = session.exec(select(TrainStop).where(TrainStop.train_id == data.train_id,
                                                     TrainStop.station_id == data.source_station_id)).first()
    if not src_stop:
        raise HTTPException(status_code=400, detail="Source station is not a stop on this train")

    dst_stop = session.exec(select(TrainStop).where(TrainStop.train_id == data.train_id,
                                                     TrainStop.station_id == data.destination_station_id)).first()
    if not dst_stop:
        raise HTTPException(status_code=400, detail="Destination station is not a stop on this train")

    if src_stop.stop_order >= dst_stop.stop_order:
        raise HTTPException(status_code=400,
                            detail="Source must come before destination on this train's route")

    n = len(data.passengers)
    inv = _get_or_create_inventory(data.train_id, data.train_class_id, data.journey_date,
                                    tc.total_seats, session)
    if inv.available_seats < n:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Only {inv.available_seats} seats available, requested {n}")

    total_fare = round(tc.fare_per_km * 500 * n, 2)

    # Generate unique PNR
    pnr = None
    for _ in range(10):
        candidate = generate_pnr()
        if not session.exec(select(Booking).where(Booking.pnr == candidate)).first():
            pnr = candidate
            break
    if not pnr:
        raise HTTPException(status_code=500, detail="Failed to generate unique PNR. Retry.")

    booking = Booking(pnr=pnr, user_id=user.id, train_id=data.train_id,
                      train_class_id=data.train_class_id,
                      source_station_id=data.source_station_id,
                      destination_station_id=data.destination_station_id,
                      journey_date=data.journey_date, total_fare=total_fare,
                      seats_booked=n, status="CONFIRMED")
    session.add(booking)
    session.flush()

    passengers = []
    for i, p in enumerate(data.passengers):
        bp = BookingPassenger(booking_id=booking.id, name=p.name, age=p.age,
                              gender=p.gender,
                              seat_number=f"{tc.class_code}{inv.booked_seats + i + 1}")
        session.add(bp)
        passengers.append(bp)

    inv.booked_seats += n
    inv.available_seats -= n
    session.add(inv)

    payment = Payment(booking_id=booking.id, amount=total_fare, payment_method="MOCK_UPI",
                      payment_status="SUCCESS",
                      transaction_id=f"RC-TXN-{uuid.uuid4().hex[:12].upper()}",
                      note="SIMULATED PAYMENT — No real money involved")
    session.add(payment)
    session.commit()
    session.refresh(booking)
    session.refresh(payment)

    src_st = session.get(Station, data.source_station_id)
    dst_st = session.get(Station, data.destination_station_id)

    return BookingResponse(
        id=booking.id, pnr=booking.pnr, train_number=train.train_number, train_name=train.name,
        source_station=src_st.code if src_st else str(data.source_station_id),
        destination_station=dst_st.code if dst_st else str(data.destination_station_id),
        journey_date=booking.journey_date, class_code=tc.class_code,
        total_fare=booking.total_fare, seats_booked=booking.seats_booked, status=booking.status,
        passengers=[PassengerResponse(id=p.id, name=p.name, age=p.age, gender=p.gender,
                                      seat_number=p.seat_number) for p in passengers],
        payment=PaymentResponse(transaction_id=payment.transaction_id, amount=payment.amount,
                                payment_method=payment.payment_method,
                                payment_status=payment.payment_status, note=payment.note),
        booked_at=booking.booked_at, cancelled_at=booking.cancelled_at,
    )


def get_booking_by_pnr(pnr: str, user: User, session: Session) -> BookingResponse:
    booking = session.exec(select(Booking).where(Booking.pnr == pnr)).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role != "admin" and booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _build_response(booking, session)


def get_user_bookings(user: User, session: Session) -> List[BookingResponse]:
    bookings = session.exec(
        select(Booking).where(Booking.user_id == user.id).order_by(Booking.booked_at.desc())
    ).all()
    return [_build_response(b, session) for b in bookings]


def _build_response(booking: Booking, session: Session) -> BookingResponse:
    train = session.get(Train, booking.train_id)
    tc = session.get(TrainClass, booking.train_class_id)
    src = session.get(Station, booking.source_station_id)
    dst = session.get(Station, booking.destination_station_id)
    pax = session.exec(select(BookingPassenger).where(
        BookingPassenger.booking_id == booking.id)).all()
    pay = session.exec(select(Payment).where(Payment.booking_id == booking.id)).first()

    return BookingResponse(
        id=booking.id, pnr=booking.pnr,
        train_number=train.train_number if train else "UNKNOWN",
        train_name=train.name if train else "UNKNOWN",
        source_station=src.code if src else str(booking.source_station_id),
        destination_station=dst.code if dst else str(booking.destination_station_id),
        journey_date=booking.journey_date,
        class_code=tc.class_code if tc else "UNKNOWN",
        total_fare=booking.total_fare, seats_booked=booking.seats_booked,
        status=booking.status,
        passengers=[PassengerResponse(id=p.id, name=p.name, age=p.age, gender=p.gender,
                                      seat_number=p.seat_number) for p in pax],
        payment=PaymentResponse(transaction_id=pay.transaction_id, amount=pay.amount,
                                payment_method=pay.payment_method,
                                payment_status=pay.payment_status, note=pay.note) if pay else None,
        booked_at=booking.booked_at, cancelled_at=booking.cancelled_at,
    )
