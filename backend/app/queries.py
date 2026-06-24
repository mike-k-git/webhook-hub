import uuid
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Delivery


async def event_rollups(
    session: AsyncSession, event_ids: list[uuid.UUID]
) -> dict[uuid.UUID, dict[str, int]]:
    rows = (
        await session.execute(
            select(Delivery.event_id, Delivery.status, func.count())
            .where(Delivery.event_id.in_(event_ids))
            .group_by(Delivery.event_id, Delivery.status)
        )
    ).all()

    counts: dict[uuid.UUID, dict[str, int]] = defaultdict(dict)
    for event_id, st, n in rows:
        counts[event_id][st.value] = n

    return dict(counts)
