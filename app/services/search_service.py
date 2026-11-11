from datetime import date
from typing import List
from fastapi import HTTPException
from sqlmodel import Session, select
from app.models.station import Station
from app.models.train import Train, TrainStop, TrainClass, SeatInventory
from app.schemas.train import TrainSearchResult


def search_trains(source_code: str, destination_code: str, journey_date: str,
                  session: Session) -> List[TrainSearchResult]:
    try:
        journey = date.fromisoformat(journey_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    if journey < date.today():
        raise HTTPException(status_code=400, detail="Journey date cannot be in the past")

    src = session.exec(select(Station).where(Station.code == source_code.upper(),
                                              Station.is_active == True)).first()
    if not src:
        raise HTTPException(status_code=404, detail=f"Source station '{source_code}' not found")

    dst = session.exec(select(Station).where(Station.code == destination_code.upper(),
                                              Station.is_active == True)).first()
    if not dst:
        raise HTTPException(status_code=404, detail=f"Destination station '{destination_code}' not found")

    if src.id == dst.id:
        raise HTTPException(status_code=400, detail="Source and destination cannot be the same")

    src_stops = session.exec(select(TrainStop).where(TrainStop.station_id == src.id)).all()

    results = []
    for ss in src_stops:
        ds = session.exec(select(TrainStop).where(
            TrainStop.train_id == ss.train_id,
            TrainStop.station_id == dst.id,
            TrainStop.stop_order > ss.stop_order,
        )).first()
        if not ds:
            continue
        train = session.get(Train, ss.train_id)
        if not train or not train.is_active:
            continue
        classes = session.exec(select(TrainClass).where(TrainClass.train_id == train.id)).all()
        available_classes = []
        for tc in classes:
            inv = session.exec(select(SeatInventory).where(
                SeatInventory.train_id == train.id,
                SeatInventory.train_class_id == tc.id,
                SeatInventory.journey_date == journey_date,
            )).first()
            available = inv.available_seats if inv else tc.total_seats
            fare = round(tc.fare_per_km * 500, 2)  # mock 500 km
            available_classes.append({
                "class_id": tc.id,
                "class_code": tc.class_code,
                "class_name": tc.class_name,
                "available_seats": available,
                "fare_per_person": fare,
            })
        results.append(TrainSearchResult(
            train_id=train.id,
            train_number=train.train_number,
            train_name=train.name,
            train_type=train.train_type,
            source_station=src.code,
            source_city=src.city,
            departure_time=ss.departure_time or "N/A",
            destination_station=dst.code,
            destination_city=dst.city,
            arrival_time=ds.arrival_time or "N/A",
            journey_date=journey_date,
            available_classes=available_classes,
        ))
    return results
