from typing import List
from fastapi import HTTPException, status
from sqlmodel import Session, select
from app.models.train import Train, TrainStop, TrainClass
from app.models.station import Station
from app.schemas.train import TrainCreate, TrainUpdate, TrainStopCreate, TrainClassCreate


def create_train(data: TrainCreate, session: Session) -> Train:
    if session.exec(select(Train).where(Train.train_number == data.train_number)).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Train number '{data.train_number}' already exists")
    train = Train(**data.model_dump())
    session.add(train)
    session.commit()
    session.refresh(train)
    return train


def get_all_trains(session: Session, active_only: bool = True) -> List[Train]:
    q = select(Train)
    if active_only:
        q = q.where(Train.is_active == True)
    return list(session.exec(q).all())


def get_train_by_id(train_id: int, session: Session) -> Train:
    t = session.get(Train, train_id)
    if not t:
        raise HTTPException(status_code=404, detail="Train not found")
    return t


def update_train(train_id: int, data: TrainUpdate, session: Session) -> Train:
    train = get_train_by_id(train_id, session)
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(train, k, v)
    session.add(train)
    session.commit()
    session.refresh(train)
    return train


def add_train_stop(train_id: int, data: TrainStopCreate, session: Session) -> TrainStop:
    get_train_by_id(train_id, session)
    station = session.get(Station, data.station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    if not station.is_active:
        raise HTTPException(status_code=400, detail="Station is not active")
    if session.exec(select(TrainStop).where(TrainStop.train_id == train_id,
                                             TrainStop.stop_order == data.stop_order)).first():
        raise HTTPException(status_code=409, detail=f"Stop order {data.stop_order} already exists")
    if session.exec(select(TrainStop).where(TrainStop.train_id == train_id,
                                             TrainStop.station_id == data.station_id)).first():
        raise HTTPException(status_code=409, detail="Station already added to this train")
    stop = TrainStop(train_id=train_id, **data.model_dump())
    session.add(stop)
    session.commit()
    session.refresh(stop)
    return stop


def get_train_stops(train_id: int, session: Session) -> List[TrainStop]:
    return list(session.exec(
        select(TrainStop).where(TrainStop.train_id == train_id).order_by(TrainStop.stop_order)
    ).all())


def add_train_class(train_id: int, data: TrainClassCreate, session: Session) -> TrainClass:
    get_train_by_id(train_id, session)
    if session.exec(select(TrainClass).where(TrainClass.train_id == train_id,
                                              TrainClass.class_code == data.class_code)).first():
        raise HTTPException(status_code=409, detail=f"Class '{data.class_code}' already exists for this train")
    tc = TrainClass(train_id=train_id, **data.model_dump())
    session.add(tc)
    session.commit()
    session.refresh(tc)
    return tc


def get_train_classes(train_id: int, session: Session) -> List[TrainClass]:
    return list(session.exec(select(TrainClass).where(TrainClass.train_id == train_id)).all())
