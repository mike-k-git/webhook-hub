from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionDep
from app.models import Delivery, DeliveryStatus
from app.schemas import DeliveryInboxItem, DeliveryRead, EventRead

router = APIRouter(prefix="/deliveries/dead_letter", tags=["deliveries"])


@router.get("", response_model=list[DeliveryInboxItem])
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
