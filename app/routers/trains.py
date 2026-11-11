from typing import List
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.database.engine import get_session
from app.schemas.train import TrainSearchResult
from app.services import search_service

router = APIRouter(prefix="/api/v1/trains", tags=["Trains — Public"])


@router.get("/search", response_model=List[TrainSearchResult])
def search_trains(
    from_station: str = Query(..., description="Source station code, e.g. NDLS"),
    to_station: str = Query(..., description="Destination station code, e.g. BCT"),
    journey_date: str = Query(..., description="Date in YYYY-MM-DD format"),
    session: Session = Depends(get_session),
):
    """Search available trains between two stations on a given date."""
    return search_service.search_trains(from_station, to_station, journey_date, session)
