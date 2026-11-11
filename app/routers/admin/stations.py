from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database.engine import get_session
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.station import StationCreate, StationUpdate, StationResponse
from app.services import station_service

router = APIRouter(prefix="/api/v1/admin/stations", tags=["Admin — Stations"])


@router.post("/", response_model=StationResponse, status_code=201)
def create_station(data: StationCreate, session: Session = Depends(get_session),
                   admin: User = Depends(require_admin)):
    return station_service.create_station(data, session)


@router.get("/", response_model=List[StationResponse])
def list_stations(session: Session = Depends(get_session),
                  admin: User = Depends(require_admin)):
    return station_service.get_all_stations(session, active_only=False)


@router.get("/{station_id}", response_model=StationResponse)
def get_station(station_id: int, session: Session = Depends(get_session),
                admin: User = Depends(require_admin)):
    return station_service.get_station_by_id(station_id, session)


@router.patch("/{station_id}", response_model=StationResponse)
def update_station(station_id: int, data: StationUpdate,
                   session: Session = Depends(get_session),
                   admin: User = Depends(require_admin)):
    return station_service.update_station(station_id, data, session)
