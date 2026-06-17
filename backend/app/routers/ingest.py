from datetime import UTC, datetime
import hashlib
import json
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db import SessionDep
from app.models import Delivery, Destination, Event, Route, Source
from app.routers import destinations
from app.schemas import IngestAck
from app.security import verify

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post(
    "/{source_name}",
    response_model=IngestAck,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest(
    source_name: str,
    request: Request,
    session: SessionDep,
    response: Response,
    x_webhook_signature: Annotated[str | None, Header()] = None,
    idempotency_key: Annotated[str | None, Header()] = None,
) -> IngestAck:
    raw = await request.body()

    source = (
        await session.execute(select(Source).where(Source.name == source_name))
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="unknown source")

    if not verify(source.signing_secret, raw, x_webhook_signature):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid signature")

    key = idempotency_key or hashlib.sha256(raw).hexdigest()
    source_id = source.id

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="invalid JSON body"
        ) from exc

    event = Event(
        source_id=source_id,
        idempotency_key=key,
        event_type=payload.get("type") if isinstance(payload, dict) else None,
        payload=payload,
        headers=dict(request.headers),
    )
    session.add(event)
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        existing = (
            await session.execute(
                select(Event).where(
                    Event.source_id == source_id,
                    Event.idempotency_key == key,
                )
            )
        ).scalar_one()
        response.status_code = status.HTTP_200_OK
        return IngestAck(event_id=existing.id)

    destination_ids = (
        (
            await session.execute(
                select(Route.destination_id).where(Route.source_id == source_id)
            )
        )
        .scalars()
        .all()
    )

    now = datetime.now(UTC)
    for dest_id in destination_ids:
        session.add(
            Delivery(event_id=event.id, destination_id=dest_id, next_attempt_at=now)
        )

    await session.commit()
    return IngestAck(event_id=event.id)
