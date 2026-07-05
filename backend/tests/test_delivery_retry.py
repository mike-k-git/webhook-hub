from datetime import UTC, datetime, timedelta

import httpx
from pytest import approx
from sqlalchemy import delete, select, text, update
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Delivery, DeliveryStatus, Destination
from app.tasks import (
    DeliveryResult,
    DeliverySnapshot,
    compute_backoff,
    deliver,
    sweep,
)
from tests.fakes import (
    FakeQueue,
    ctx,
    fail_result,
    fake_rng,
    reclaiming_send,
    send_fn,
)


def test_backoff_schedule():
    pre_computed_backoff = [2, 4, 8, 16, 32, 60, 60]

    for i in range(7):
        assert compute_backoff(i, 2, 2, 60, fake_rng) == pre_computed_backoff[i]


async def test_cap_boundary_last_retry_stays_failed(
    make_delivery, sessionmaker_factory, monkeypatch
):
    monkeypatch.setattr(settings, "max_attempts", 3)
    delivery = await make_delivery(
        status=DeliveryStatus.failed,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    results: list[DeliveryResult] = [fail_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            ctx(client=worker_client, sessionmaker=sessionmaker_factory),
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
        assert updated_delivery.status == DeliveryStatus.failed
        assert updated_delivery.attempt_count == 2
        assert len(calls) == 1
        assert len(updated_delivery.attempts) == 2


async def test_cap_boundary_flips_to_dead_letter(
    make_delivery, sessionmaker_factory, monkeypatch
):
    monkeypatch.setattr(settings, "max_attempts", 3)
    delivery = await make_delivery(
        status=DeliveryStatus.failed,
        attempt_count=2,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    results: list[DeliveryResult] = [fail_result()]
    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            ctx(client=worker_client, sessionmaker=sessionmaker_factory),
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
        assert updated_delivery.status == DeliveryStatus.dead_letter
        assert updated_delivery.attempt_count == 3
        assert len(calls) == 1
        assert len(updated_delivery.attempts) == 2


async def test_terminal_is_inert(make_delivery, sessionmaker_factory):
    delivery = await make_delivery(
        status=DeliveryStatus.dead_letter,
        attempt_count=1,
        next_attempt_at=None,
    )

    fake_queue = FakeQueue()
    c = ctx(queue=fake_queue, sessionmaker=sessionmaker_factory)

    await sweep(c)

    assert len(fake_queue.enqueued) == 0

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.status == DeliveryStatus.dead_letter
        assert updated_delivery.attempt_count == 1
        assert len(updated_delivery.attempts) == 1


async def test_fence_drops_stale_finalize(make_delivery, sessionmaker_factory):
    delivery = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    a_calls, b_calls = [], []

    async with httpx.AsyncClient() as client:
        await deliver(
            ctx(client=client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=reclaiming_send(sessionmaker_factory, delivery, a_calls, b_calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.status == DeliveryStatus.succeeded
        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.attempt_count == 1
        assert len(updated_delivery.attempts) == 1
        assert len(a_calls) == 1 and len(b_calls) == 1


async def test_fence_orphaned_double_dispatch(make_delivery, sessionmaker_factory):
    delivery = await make_delivery(
        status=DeliveryStatus.delivering,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=settings.lease),
    )

    a_calls, b_calls = [], []

    async with httpx.AsyncClient() as client:
        await deliver(
            ctx(client=client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=reclaiming_send(sessionmaker_factory, delivery, a_calls, b_calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.status == DeliveryStatus.succeeded
        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.attempt_count == 2
        assert len(updated_delivery.attempts) == 2
        assert len(a_calls) == 1 and len(b_calls) == 1


async def test_missing_destination_flips_to_dead_letter(
    make_delivery, sessionmaker_factory
):
    delivery = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    async with sessionmaker_factory() as s:
        await s.execute(text("SET LOCAL session_replication_role = replica"))
        await s.execute(
            delete(Destination).where(Destination.id == delivery.destination_id)
        )
        await s.commit()

    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as client:
        await deliver(
            ctx(client=client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn([fail_result()], calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.status == DeliveryStatus.dead_letter
        assert updated_delivery.next_attempt_at is None
        assert updated_delivery.attempt_count == 0
        assert len(updated_delivery.attempts) == 1
        assert updated_delivery.attempts[0].attempt_number == 0
        assert updated_delivery.attempts[0].error == "destination row missing"
        assert len(calls) == 0


async def test_destination_is_not_active(
    make_delivery, sessionmaker_factory, monkeypatch
):
    monkeypatch.setattr(settings, "inactive_hold_seconds", 900)
    delivery = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    async with sessionmaker_factory() as s:
        await s.execute(
            update(Destination)
            .where(Destination.id == delivery.destination_id)
            .values(active=False)
        )
        await s.commit()

    calls: list[DeliverySnapshot] = []

    async with httpx.AsyncClient() as client:
        await deliver(
            ctx(client=client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn([], calls),
        )

    async with sessionmaker_factory() as check:
        updated_delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_delivery.status == DeliveryStatus.pending
        assert updated_delivery.next_attempt_at == approx(
            datetime.now(UTC) + timedelta(seconds=settings.inactive_hold_seconds),
            abs=timedelta(seconds=1),
        )
        assert updated_delivery.attempt_count == 0
        assert len(updated_delivery.attempts) == 0
        assert len(calls) == 0
