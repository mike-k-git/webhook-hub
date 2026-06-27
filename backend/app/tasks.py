import datetime as dt
import uuid
from dataclasses import dataclass
from typing import Awaitable, Callable

import httpx
from saq import CronJob, Queue
from saq.types import Context, SettingsDict
from sqlalchemy import and_, func, or_, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings as app_settings
from app.db import AsyncSessionLocal
from app.models import Delivery, DeliveryAttempt, DeliveryStatus

LEASE = 60
FIXED_DELAY = 100


class WorkerContext(Context):
    client: httpx.AsyncClient
    sessionmaker: async_sessionmaker[AsyncSession]


@dataclass
class DeliveryResult:
    success: bool
    response_status: int | None = None
    response_body: str | None = None
    error: str | None = None
    duration_ms: int = 0


@dataclass(frozen=True)
class DeliverySnapshot:
    attempt_count: int
    destination_id: uuid.UUID
    event_id: uuid.UUID


SendFn = Callable[[DeliverySnapshot], Awaitable[DeliveryResult]]


async def _real_send(delivery_context: DeliverySnapshot) -> DeliveryResult:
    raise NotImplementedError


async def success_stub(ctx: DeliverySnapshot) -> DeliveryResult:
    return DeliveryResult(
        success=False, response_status=200, response_body="ok", duration_ms=10
    )


async def deliver(
    ctx: WorkerContext, *, delivery_id: str, send_fn: SendFn = success_stub
) -> None:
    event_delivery_id = uuid.UUID(delivery_id)

    async with ctx["sessionmaker"]() as session:
        row = (
            await session.execute(
                update(Delivery)
                .where(
                    and_(
                        Delivery.id == event_delivery_id,
                        or_(
                            and_(
                                Delivery.status == DeliveryStatus.pending,
                                or_(
                                    Delivery.next_attempt_at.is_(None),
                                    Delivery.next_attempt_at <= func.now(),
                                ),
                            ),
                            and_(
                                Delivery.status == DeliveryStatus.delivering,
                                Delivery.updated_at
                                <= func.now() - dt.timedelta(seconds=LEASE),
                            ),
                        ),
                    )
                )
                .values(status=DeliveryStatus.delivering)
                .returning(
                    Delivery.attempt_count,
                    Delivery.destination_id,
                    Delivery.event_id,
                )
            )
        ).one_or_none()

        if row is None:
            return

        attempt_count = row.attempt_count
        destination_id = row.destination_id
        event_id = row.event_id

        await session.commit()

    result = await send_fn(
        DeliverySnapshot(
            attempt_count=attempt_count,
            destination_id=destination_id,
            event_id=event_id,
        )
    )

    async with ctx["sessionmaker"]() as session:
        attempt = DeliveryAttempt(
            delivery_id=event_delivery_id,
            attempt_number=attempt_count + 1,
            response_status=result.response_status,
            response_body=result.response_body,
            error=result.error,
            duration_ms=result.duration_ms,
        )

        session.add(attempt)

        stmt = update(Delivery).where(Delivery.id == event_delivery_id)

        if result.success:
            await session.execute(
                stmt.values(
                    status=DeliveryStatus.succeeded, attempt_count=attempt_count + 1
                )
            )

        else:
            await session.execute(
                stmt.values(
                    status=DeliveryStatus.failed,
                    next_attempt_at=func.now() + dt.timedelta(seconds=FIXED_DELAY),
                    attempt_count=attempt_count + 1,
                )
            )

        await session.commit()


async def sweep(ctx: WorkerContext) -> None:
    print("sweeper")


async def startup(ctx: WorkerContext) -> None:
    ctx["client"] = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0), follow_redirects=False
    )
    ctx["sessionmaker"] = AsyncSessionLocal


async def shutdown(ctx: WorkerContext) -> None:
    await ctx["client"].aclose()


queue = Queue.from_url(str(app_settings.redis_dsn))

settings: SettingsDict[WorkerContext] = SettingsDict(
    queue=queue,
    functions=[deliver],
    concurrency=10,
    cron_jobs=[CronJob(sweep, cron="* * * * * */5")],
    startup=startup,
    shutdown=shutdown,
)
