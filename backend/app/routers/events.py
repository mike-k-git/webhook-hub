from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.db import SessionDep
from app.models import Event
from app.schemas import EventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
async def list_events(
    session: SessionDep, limit: Annotated[int, Query(le=200)] = 50
) -> list[Event]:
    result = await session.execute(
        select(Event).order_by(Event.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
