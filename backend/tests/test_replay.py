import uuid

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import get_queue
from app.main import app, settings
from app.models import Delivery, DeliveryStatus, Event
from app.tasks import deliver
from tests.fakes import FakeRaisingQueue, ctx, fail_result, ok_result, send_fn


async def test_replay_accepted(client, make_delivery, sessionmaker_factory):
    d = await make_delivery(
        status=DeliveryStatus.dead_letter, next_attempt_at=None, attempt_count=1
    )

    r = await client.post(f"/deliveries/{d.id}/replay")
    assert r.status_code == 202

    async with sessionmaker_factory() as s:
        updated_d = (
            await s.execute(select(Delivery).where(Delivery.id == d.id))
        ).scalar_one()

        assert updated_d.status == DeliveryStatus.pending
        assert updated_d.next_attempt_at is None
        assert updated_d.locked_by is None
        assert updated_d.locked_until is None


@pytest.mark.parametrize(
    "status",
    [
        DeliveryStatus.pending,
        DeliveryStatus.delivering,
        DeliveryStatus.failed,
        DeliveryStatus.succeeded,
    ],
)
async def test_replay_conflict_status(
    status, client, make_delivery, sessionmaker_factory
):
    d = await make_delivery(status=status, next_attempt_at=None, attempt_count=1)
    r = await client.post(f"/deliveries/{d.id}/replay")

    assert r.status_code == 409

    async with sessionmaker_factory() as s:
        updated_d = (
            await s.execute(select(Delivery).where(Delivery.id == d.id))
        ).scalar_one()

        assert updated_d.status == status
        assert updated_d.next_attempt_at is None
        assert updated_d.attempt_count == 1
        assert updated_d.locked_by is None
        assert updated_d.locked_until is None


async def test_replay_unknown_delivery(client):
    r = await client.post(f"/deliveries/{uuid.uuid4()}/replay")

    assert r.status_code == 404


async def test_oneshot_boundary(
    client, make_delivery, monkeypatch, sessionmaker_factory
):
    monkeypatch.setattr(settings, "max_attempts", 3)
    d = await make_delivery(
        status=DeliveryStatus.dead_letter, next_attempt_at=None, attempt_count=3
    )
    r = await client.post(f"/deliveries/{d.id}/replay")
    assert r.status_code == 202

    async with httpx.AsyncClient() as w:
        await deliver(
            ctx(client=w, sessionmaker=sessionmaker_factory),
            delivery_id=str(d.id),
            send_fn=send_fn([fail_result()], []),
        )

    async with sessionmaker_factory() as s:
        updated_d = (
            await s.execute(
                select(Delivery)
                .where(Delivery.id == d.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_d.status == DeliveryStatus.dead_letter
        assert updated_d.attempt_count == 4
        assert len(updated_d.attempts) == 2
        assert (
            max(updated_d.attempts, key=lambda a: a.attempt_number).attempt_number == 4
        )


async def test_replay_to_success(client, make_delivery, sessionmaker_factory):
    d = await make_delivery(
        status=DeliveryStatus.dead_letter, next_attempt_at=None, attempt_count=1
    )
    r = await client.post(f"/deliveries/{d.id}/replay")
    assert r.status_code == 202

    async with httpx.AsyncClient() as w:
        await deliver(
            ctx(client=w, sessionmaker=sessionmaker_factory),
            delivery_id=str(d.id),
            send_fn=send_fn([ok_result()], []),
        )

    async with sessionmaker_factory() as s:
        updated_d = (
            await s.execute(
                select(Delivery)
                .where(Delivery.id == d.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_d.status == DeliveryStatus.succeeded
        assert updated_d.attempt_count == 2
        assert (
            max(updated_d.attempts, key=lambda a: a.attempt_number).attempt_number == 2
        )


async def test_routes_snapshot(client, make_delivery, sessionmaker_factory):
    d = await make_delivery(
        status=DeliveryStatus.dead_letter, next_attempt_at=None, attempt_count=1
    )

    async with sessionmaker_factory() as s:
        event = (
            await s.execute(select(Event).where(Event.id == d.event_id))
        ).scalar_one()

    dst = (
        await client.post("/destinations", json={"name": "d1", "url": "http://a.test"})
    ).json()["id"]

    await client.post(
        "/routes", json={"source_id": str(event.source_id), "destination_id": dst}
    )

    r = await client.post(f"/deliveries/{d.id}/replay")
    assert r.status_code == 202

    async with sessionmaker_factory() as s:
        updated_d = (
            await s.execute(
                select(Delivery)
                .where(Delivery.id == d.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        n = await s.scalar(
            select(func.count())
            .select_from(Delivery)
            .where(Delivery.event_id == d.event_id)
        )
        assert n == 1
        assert updated_d.status == DeliveryStatus.pending
        assert updated_d.attempt_count == 1
        assert len(updated_d.attempts) == 1
        assert updated_d.attempts[0].delivery_id == d.id


async def test_enqueu_raises(client, make_delivery, sessionmaker_factory):
    app.dependency_overrides[get_queue] = lambda: FakeRaisingQueue(set(), fail_all=True)
    d = await make_delivery(
        status=DeliveryStatus.dead_letter, next_attempt_at=None, attempt_count=1
    )
    r = await client.post(f"/deliveries/{d.id}/replay")
    assert r.status_code == 202

    async with sessionmaker_factory() as s:
        updated_d = (
            await s.execute(
                select(Delivery)
                .where(Delivery.id == d.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert updated_d.status == DeliveryStatus.pending
        assert updated_d.attempt_count == 1
