import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Event, Source
from app.schemas import IngestAck

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post(
    "/{source_name}",
    response_model=IngestAck,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest(
    source_name: str, request: Request, session: AsyncSession = Depends(get_session)
) -> IngestAck:
    raw = await request.body()

    source = (
        await session.execute(select(Source).where(Source.name == source_name))
    ).scalar_one_or_none()
    if source is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="unknown source")

    idempotency_key = (
        request.headers.get("idempotency-key") or hashlib.sha256(raw).hexdigest()
    )

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="invalid JSON body")

    event = Event(
        source_id=source.id,
        idempotency_key=idempotency_key,
        event_type=payload.get("type") if isinstance(payload, dict) else None,
        payload=payload,
        headers=dict(request.headers),
    )
    session.add(event)
    await session.commit()

    return IngestAck(event_id=event.id)
