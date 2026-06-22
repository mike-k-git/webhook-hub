import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionDep
from app.models import Delivery, Event
from app.schemas import EventDetailRead, EventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
async def list_events(
    session: SessionDep, limit: Annotated[int, Query(le=200)] = 50
) -> list[Event]:
    result = await session.execute(
        select(Event).order_by(Event.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{event_id}", response_model=EventDetailRead)
async def event_detail(event_id: uuid.UUID, session: SessionDep):
    event = (
        (
            await session.execute(
                select(Event)
                .where(Event.id == event_id)
                .options(selectinload(Event.deliveries).selectinload(Delivery.attempts))
            )
        )
        .scalars()
        .one_or_none()
    )

    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "unknown event")
    return event
