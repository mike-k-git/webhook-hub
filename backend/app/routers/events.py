import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, tuple_
from sqlalchemy.orm import selectinload

from app.deps import SessionDep
from app.models import Delivery, DeliveryStatus, Event, Source
from app.pagination import CursorError, decode_cursor, encode_cursor
from app.queries import event_rollups
from app.schemas import (
    EventDetailRead,
    EventListItem,
    EventListResponse,
    RollupRead,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=EventListResponse)
async def list_events(
    session: SessionDep,
    limit: Annotated[int, Query(le=200)] = 50,
    cursor: str | None = None,
    source: str | None = None,
    delivery_status: Annotated[DeliveryStatus | None, Query(alias="status")] = None,
) -> EventListResponse:

    stmt = (
        select(Event)
        .order_by(Event.received_at.desc(), Event.id.desc())
        .limit(limit + 1)
    )

    if source is not None:
        stmt = stmt.where(
            Event.source_id
            == select(Source.id).where(Source.name == source).scalar_subquery()
        )

    if delivery_status is not None:
        stmt = stmt.where(
            select(Delivery)
            .where(Delivery.event_id == Event.id, Delivery.status == delivery_status)
            .exists()
        )

    if cursor is not None:
        try:
            cursor_ts, cursor_id = decode_cursor(cursor)
        except CursorError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="invalid cursor"
            ) from exc
        stmt = stmt.where(tuple_(Event.received_at, Event.id) < (cursor_ts, cursor_id))

    result = await session.execute(stmt)
    events = list(result.scalars().all())
    has_more = len(events) > limit
    events = events[:limit]
    next_cursor = None
    if has_more:
        last = events[-1]
        next_cursor = encode_cursor(last.received_at, last.id)

    event_ids = [e.id for e in events]
    counts = await event_rollups(session, event_ids)
    items = [
        EventListItem(
            id=e.id,
            source_id=e.source_id,
            event_type=e.event_type,
            idempotency_key=e.idempotency_key,
            received_at=e.received_at,
            rollup=RollupRead(
                total=sum(counts.get(e.id, {}).values()),
                counts_by_status=counts.get(e.id, {}),
            ),
        )
        for e in events
    ]
    return EventListResponse(items=items, next_cursor=next_cursor)


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
