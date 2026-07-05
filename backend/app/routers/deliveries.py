import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, select, update
from sqlalchemy.orm import selectinload

from app.db import SessionDep
from app.models import Delivery, DeliveryStatus
from app.schemas import DeliveryInboxItem, DeliveryRead, EventRead

router = APIRouter(prefix="/deliveries", tags=["deliveries"])


@router.post("/{delivery_id}/replay", status_code=status.HTTP_202_ACCEPTED)
async def replay(delivery_id: uuid.UUID, session: SessionDep):
    owner = (
        await session.execute(
            update(Delivery)
            .where(
                and_(
                    Delivery.id == delivery_id,
                    Delivery.status == DeliveryStatus.dead_letter,
                )
            )
            .values(
                status=DeliveryStatus.pending,
                next_attempt_at=None,
                locked_by=None,
                locked_until=None,
            )
            .returning(Delivery.id)
        )
    ).one_or_none()

    if owner is not None:
        await session.commit()
        return

    delivery = (
        await session.execute(select(Delivery).where(Delivery.id == delivery_id))
    ).scalar_one_or_none()

    if delivery is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="unknown delivery")

    raise HTTPException(status.HTTP_409_CONFLICT, detail=f"{delivery.status.value}")


@router.get("/dead_letter", response_model=list[DeliveryInboxItem])
async def inbox(
    session: SessionDep,
    limit: Annotated[int, Query(le=200)] = 50,
) -> list[DeliveryInboxItem]:
    deliveries = (
        (
            await session.execute(
                select(Delivery)
                .where(Delivery.status == DeliveryStatus.dead_letter)
                .order_by(Delivery.updated_at.desc(), Delivery.id.desc())
                .options(selectinload(Delivery.attempts), selectinload(Delivery.event))
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )

    items = [
        DeliveryInboxItem(
            delivery=DeliveryRead.model_validate(d),
            event=EventRead.model_validate(d.event),
        )
        for d in deliveries
    ]
    return items
