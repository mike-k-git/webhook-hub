import asyncio
from datetime import UTC, datetime, timedelta
from typing import cast

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Delivery, DeliveryStatus
from app.tasks import DeliveryResult, DeliverySnapshot, WorkerContext, deliver
from tests.fakes import send_fn


def _ctx(*, client, sessionmaker) -> WorkerContext:
    return cast(WorkerContext, {"client": client, "sessionmaker": sessionmaker})


def _ok_result() -> DeliveryResult:
    return DeliveryResult(
        success=True, response_status=200, response_body="", error=None, duration_ms=10
    )


async def test_claims_pending_row(make_delivery, sessionmaker_factory):
    delivery = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    results: list[DeliveryResult] = [_ok_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            _ctx(client=worker_client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn(results, calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.status == DeliveryStatus.succeeded
        assert updated_delivery.attempt_count == 1
        assert len(updated_delivery.attempts) == 1
        assert updated_delivery.attempts[0].response_status == 200
        assert len(calls) == 1
        assert len(results) == 0


async def test_claims_nextattemptat_null_pending_row(
    make_delivery, sessionmaker_factory
):
    delivery = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=None,
    )

    results: list[DeliveryResult] = [_ok_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            _ctx(client=worker_client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn(results, calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.status == DeliveryStatus.succeeded
        assert updated_delivery.attempt_count == 1
        assert len(updated_delivery.attempts) == 1
        assert updated_delivery.attempts[0].response_status == 200
        assert len(calls) == 1
        assert len(results) == 0


async def test_does_not_claim_future_scheduled_row(make_delivery, sessionmaker_factory):
    next_attempt = datetime.now(UTC) + timedelta(minutes=1)
    delivery = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=next_attempt,
    )

    results: list[DeliveryResult] = [_ok_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            _ctx(client=worker_client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn(results, calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at == next_attempt
        assert updated_delivery.status == DeliveryStatus.pending
        assert updated_delivery.attempt_count == 0
        assert len(updated_delivery.attempts) == 0
        assert len(calls) == 0
        assert len(results) == 1


async def test_does_not_claim_already_claimed(make_delivery, sessionmaker_factory):
    half_lease = timedelta(seconds=settings.lease / 2)
    delivery = await make_delivery(
        status=DeliveryStatus.delivering,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC) + half_lease,
        updated_at=datetime.now(UTC) - half_lease,
    )

    results: list[DeliveryResult] = [_ok_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            _ctx(client=worker_client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn(results, calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at is not None
        assert updated_delivery.status == DeliveryStatus.delivering
        assert updated_delivery.attempt_count == 1
        assert len(updated_delivery.attempts) == 1
        assert len(calls) == 0
        assert len(results) == 1


async def test_claims_orphaned_row(make_delivery, sessionmaker_factory):
    delivery = await make_delivery(
        status=DeliveryStatus.delivering,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC),
        updated_at=datetime.now(UTC) - timedelta(seconds=settings.lease * 5),
    )

    results: list[DeliveryResult] = [_ok_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            _ctx(client=worker_client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn(results, calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.status == DeliveryStatus.succeeded
        assert updated_delivery.attempt_count == 2
        assert len(updated_delivery.attempts) == 2
        assert len(calls) == 1
        assert len(results) == 0


async def test_atomic_claim_under_concurrency(make_delivery, sessionmaker_factory):
    delivery = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC),
    )

    results: list[DeliveryResult] = [_ok_result(), _ok_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        ctx = _ctx(client=worker_client, sessionmaker=sessionmaker_factory)

        await asyncio.gather(
            deliver(
                ctx,
                delivery_id=str(delivery.id),
                send_fn=send_fn(results, calls),
            ),
            deliver(
                ctx,
                delivery_id=str(delivery.id),
                send_fn=send_fn(results, calls),
            ),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.status == DeliveryStatus.succeeded
        assert updated_delivery.attempt_count == 1
        assert len(updated_delivery.attempts) == 1
        assert len(calls) == 1
        assert len(results) == 1


async def test_claims_failed_row(make_delivery, sessionmaker_factory):
    past_lease = timedelta(seconds=settings.lease * 2)
    delivery = await make_delivery(
        status=DeliveryStatus.failed,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC) - past_lease,
        updated_at=datetime.now(UTC) - past_lease,
    )

    results: list[DeliveryResult] = [_ok_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            _ctx(client=worker_client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn(results, calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.status == DeliveryStatus.succeeded
        assert updated_delivery.attempt_count == 2
        assert len(updated_delivery.attempts) == 2
        assert len(calls) == 1
        assert len(results) == 0
