import datetime as dt
import logging
import random
import uuid
from dataclasses import dataclass
from time import perf_counter
from typing import Awaitable, Callable

import httpx
from saq import CronJob, Queue
from saq.types import Context, SettingsDict
from sqlalchemy import ColumnElement, and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings as app_settings
from app.db import AsyncSessionLocal
from app.models import Delivery, DeliveryAttempt, DeliveryStatus, Destination, Event

logger = logging.getLogger(__name__)


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
    url: str
    payload: dict


SendFn = Callable[[httpx.AsyncClient, DeliverySnapshot], Awaitable[DeliveryResult]]


async def _real_send(
    client: httpx.AsyncClient, snapshot: DeliverySnapshot
) -> DeliveryResult:
    start = perf_counter()
    try:
        resp = await client.post(snapshot.url, json=snapshot.payload)
    except httpx.RequestError as exc:
        ms = int((perf_counter() - start) * 1000)
        return DeliveryResult(success=False, error=str(exc), duration_ms=ms)
    ms = int((perf_counter() - start) * 1000)
    return DeliveryResult(
        success=200 <= resp.status_code < 300,
        response_status=resp.status_code,
        response_body=resp.text[: app_settings.body_cap],
        duration_ms=ms,
    )


def claimable() -> ColumnElement[bool]:
    return or_(
        and_(
            Delivery.status.in_([DeliveryStatus.pending, DeliveryStatus.failed]),
            or_(
                Delivery.next_attempt_at.is_(None),
                Delivery.next_attempt_at <= func.now(),
            ),
        ),
        and_(
            Delivery.status == DeliveryStatus.delivering,
            or_(
                Delivery.locked_until.is_(None),
                Delivery.locked_until <= func.now(),
            ),
        ),
    )


def compute_backoff(
    attempt_index: int,
    base: float,
    factor: float,
    ceiling: float,
    rng: Callable[[float, float], float] = random.uniform,
) -> float:
    return rng(0, min(base * factor**attempt_index, ceiling))


async def deliver(
    ctx: WorkerContext,
    *,
    delivery_id: str,
    send_fn: SendFn = _real_send,
    rng: Callable[[float, float], float] = random.uniform,
) -> None:
    event_delivery_id = uuid.UUID(delivery_id)

    lock_token = uuid.uuid4()

    async with ctx["sessionmaker"]() as session:
        row = (
            await session.execute(
                update(Delivery)
                .where(and_(Delivery.id == event_delivery_id, claimable()))
                .values(
                    status=DeliveryStatus.delivering,
                    locked_by=lock_token,
                    locked_until=func.now() + dt.timedelta(seconds=app_settings.lease),
                )
                .returning(
                    Delivery.attempt_count,
                    Delivery.destination_id,
                    Delivery.event_id,
                )
            )
        ).one_or_none()

        if row is None:
            return

        dst = await session.get(Destination, row.destination_id)
        event = await session.get(Event, row.event_id)

        if dst is None or event is None:
            logger.error(
                "delivery %s references missing dst=%s event=%s",
                event_delivery_id,
                row.destination_id,
                row.event_id,
            )
            return

        snapshot = DeliverySnapshot(
            attempt_count=row.attempt_count,
            destination_id=row.destination_id,
            event_id=row.event_id,
            url=dst.url,
            payload=event.payload,
        )

        await session.commit()

    result = await send_fn(ctx["client"], snapshot)

    async with ctx["sessionmaker"]() as session:
        attempt = DeliveryAttempt(
            delivery_id=event_delivery_id,
            attempt_number=snapshot.attempt_count + 1,
            response_status=result.response_status,
            response_body=result.response_body,
            error=result.error,
            duration_ms=result.duration_ms,
        )

        stmt = update(Delivery).where(
            and_(Delivery.id == event_delivery_id, Delivery.locked_by == lock_token)
        )

        if result.success:
            stmt = stmt.values(
                status=DeliveryStatus.succeeded,
                next_attempt_at=None,
                attempt_count=snapshot.attempt_count + 1,
                locked_by=None,
                locked_until=None,
            ).returning(Delivery.id)
        else:
            n = row.attempt_count
            new_count = n + 1
            if new_count >= app_settings.max_attempts:
                stmt = stmt.values(
                    status=DeliveryStatus.dead_letter,
                    next_attempt_at=None,
                    attempt_count=snapshot.attempt_count + 1,
                    locked_by=None,
                    locked_until=None,
                ).returning(Delivery.id)
            else:
                delay = compute_backoff(
                    n,
                    app_settings.backoff_base,
                    app_settings.backoff_factor,
                    app_settings.backoff_ceiling,
                    rng,
                )
                stmt = stmt.values(
                    status=DeliveryStatus.failed,
                    next_attempt_at=func.now() + dt.timedelta(seconds=delay),
                    attempt_count=snapshot.attempt_count + 1,
                    locked_by=None,
                    locked_until=None,
                ).returning(Delivery.id)

        owner = (await session.execute(stmt)).one_or_none()

        if owner is None:
            logger.debug(
                "delivery %s reclaimed, dropping stale finalize", event_delivery_id
            )
            return

        session.add(attempt)
        await session.commit()


async def sweep(ctx: WorkerContext) -> None:
    async with ctx["sessionmaker"]() as session:
        redispatch = (
            (
                await session.execute(
                    select(Delivery.id)
                    .where(claimable())
                    .limit(app_settings.redispatch_limit)
                )
            )
            .scalars()
            .all()
        )

        logger.debug("%d deliveries are about to be re-dispatched", len(redispatch))

        queue = ctx["worker"].queue
        for did in redispatch:
            try:
                await queue.enqueue(
                    "deliver", delivery_id=str(did), key=f"deliver:{did}"
                )
            except Exception:
                logger.exception("failed to enqueue delivery %s", did)


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
