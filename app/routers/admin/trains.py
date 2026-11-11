from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.database.engine import get_session
from app.dependencies.auth import require_admin
from app.models.user import User
from app.models.station import Station
from app.schemas.train import (TrainCreate, TrainUpdate, TrainResponse, TrainDetailResponse,
                                TrainStopCreate, TrainStopResponse,
                                TrainClassCreate, TrainClassResponse)
from app.services import train_service

router = APIRouter(prefix="/api/v1/admin/trains", tags=["Admin — Trains"])


@router.post("/", response_model=TrainResponse, status_code=201)
def create_train(data: TrainCreate, session: Session = Depends(get_session),
                 admin: User = Depends(require_admin)):
    return train_service.create_train(data, session)


@router.get("/", response_model=List[TrainResponse])
def list_trains(session: Session = Depends(get_session),
                admin: User = Depends(require_admin)):
    return train_service.get_all_trains(session, active_only=False)


@router.get("/{train_id}", response_model=TrainDetailResponse)
def get_train(train_id: int, session: Session = Depends(get_session),
              admin: User = Depends(require_admin)):
    train = train_service.get_train_by_id(train_id, session)
    stops_db = train_service.get_train_stops(train_id, session)
    classes_db = train_service.get_train_classes(train_id, session)
    stops = []
    for s in stops_db:
        st = session.get(Station, s.station_id)
        stops.append(TrainStopResponse(id=s.id, train_id=s.train_id, station_id=s.station_id,
                                       stop_order=s.stop_order, arrival_time=s.arrival_time,
                                       departure_time=s.departure_time, day_offset=s.day_offset,
                                       station_code=st.code if st else None,
                                       station_name=st.name if st else None,
                                       city=st.city if st else None))
    return TrainDetailResponse(id=train.id, train_number=train.train_number, name=train.name,
                                train_type=train.train_type, is_active=train.is_active,
                                stops=stops,
                                classes=[TrainClassResponse.model_validate(c) for c in classes_db])


@router.patch("/{train_id}", response_model=TrainResponse)
def update_train(train_id: int, data: TrainUpdate, session: Session = Depends(get_session),
                 admin: User = Depends(require_admin)):
    return train_service.update_train(train_id, data, session)


@router.post("/{train_id}/stops", response_model=TrainStopResponse, status_code=201)
def add_stop(train_id: int, data: TrainStopCreate, session: Session = Depends(get_session),
             admin: User = Depends(require_admin)):
    stop = train_service.add_train_stop(train_id, data, session)
    st = session.get(Station, stop.station_id)
    return TrainStopResponse(id=stop.id, train_id=stop.train_id, station_id=stop.station_id,
                              stop_order=stop.stop_order, arrival_time=stop.arrival_time,
                              departure_time=stop.departure_time, day_offset=stop.day_offset,
                              station_code=st.code if st else None,
                              station_name=st.name if st else None,
                              city=st.city if st else None)


@router.get("/{train_id}/stops", response_model=List[TrainStopResponse])
def list_stops(train_id: int, session: Session = Depends(get_session),
               admin: User = Depends(require_admin)):
    stops = train_service.get_train_stops(train_id, session)
    result = []
    for s in stops:
        st = session.get(Station, s.station_id)
        result.append(TrainStopResponse(id=s.id, train_id=s.train_id, station_id=s.station_id,
                                        stop_order=s.stop_order, arrival_time=s.arrival_time,
                                        departure_time=s.departure_time, day_offset=s.day_offset,
                                        station_code=st.code if st else None,
                                        station_name=st.name if st else None,
                                        city=st.city if st else None))
    return result


@router.post("/{train_id}/classes", response_model=TrainClassResponse, status_code=201)
def add_class(train_id: int, data: TrainClassCreate, session: Session = Depends(get_session),
              admin: User = Depends(require_admin)):
    return train_service.add_train_class(train_id, data, session)


@router.get("/{train_id}/classes", response_model=List[TrainClassResponse])
def list_classes(train_id: int, session: Session = Depends(get_session),
                 admin: User = Depends(require_admin)):
    return train_service.get_train_classes(train_id, session)
