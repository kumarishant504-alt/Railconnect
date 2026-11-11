from typing import List, Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.station import Station
from app.schemas.station import StationCreate, StationUpdate


def create_station(data: StationCreate, session: Session) -> Station:
    if session.exec(select(Station).where(Station.code == data.code)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Station with code '{data.code}' already exists")
    station = Station(**data.model_dump())
    session.add(station)
    session.commit()
    session.refresh(station)
    return station


def get_all_stations(session: Session, active_only: bool = True) -> List[Station]:
    q = select(Station)
    if active_only:
        q = q.where(Station.is_active == True)
    return list(session.exec(q.order_by(Station.code)).all())


def get_station_by_id(station_id: int, session: Session) -> Station:
    s = session.get(Station, station_id)
    if not s:
        raise HTTPException(status_code=404, detail="Station not found")
    return s


def get_station_by_code(code: str, session: Session) -> Optional[Station]:
    return session.exec(select(Station).where(Station.code == code.upper())).first()


def update_station(station_id: int, data: StationUpdate, session: Session) -> Station:
    station = get_station_by_id(station_id, session)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(station, k, v)
    session.add(station)
    session.commit()
    session.refresh(station)
    return station
