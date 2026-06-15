from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Event
from app.schemas import EventRead

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
async def list_events(
    session: AsyncSession = Depends(get_session), limit: int = Query(50, le=200)
) -> list[Event]:
    result = await session.execute(
        select(Event).order_by(Event.received_at.desc()).limit(limit)
    )
    return list(result.scalars().all())
