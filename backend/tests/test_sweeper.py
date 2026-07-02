from datetime import UTC, datetime, timedelta
from typing import cast

from app.config import settings
from app.models import DeliveryStatus
from app.tasks import WorkerContext, sweep
from tests.fakes import FakeQueue, FakeRaisingQueue, FakeWorker


def _ctx(*, queue, sessionmaker) -> WorkerContext:
    return cast(
        WorkerContext, {"worker": FakeWorker(queue), "sessionmaker": sessionmaker}
    )


async def test_sweep_mix_of_rows(make_delivery, sessionmaker_factory):
    # succedeed
    await make_delivery(
        status=DeliveryStatus.succeeded,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC),
    )

    pending = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=settings.lease / 2),
    )

    failed = await make_delivery(
        status=DeliveryStatus.failed,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC) - timedelta(seconds=settings.lease * 2),
        updated_at=datetime.now(UTC) - timedelta(seconds=settings.lease * 2),
    )

    pending_null = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=None,
    )

    orphaned = await make_delivery(
        status=DeliveryStatus.delivering,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC),
        updated_at=datetime.now(UTC) - timedelta(seconds=settings.lease * 5),
    )

    # scheduled
    await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC) + timedelta(minutes=1),
    )

    # delivering
    await make_delivery(
        status=DeliveryStatus.delivering,
        attempt_count=1,
        next_attempt_at=datetime.now(UTC) + timedelta(seconds=settings.lease / 2),
        updated_at=datetime.now(UTC) - timedelta(seconds=settings.lease / 2),
    )

    fake_queue = FakeQueue()
    ctx = _ctx(queue=fake_queue, sessionmaker=sessionmaker_factory)

    await sweep(ctx)

    assert {e["delivery_id"] for e in fake_queue.enqueued} == {
        str(pending.id),
        str(failed.id),
        str(pending_null.id),
        str(orphaned.id),
    }


async def test_bounded_batch(make_delivery, sessionmaker_factory):
    for _ in range(settings.redispatch_limit + 1):
        await make_delivery(
            status=DeliveryStatus.pending,
            attempt_count=0,
            next_attempt_at=datetime.now(UTC) - timedelta(seconds=settings.lease / 2),
        )

    fake_queue = FakeQueue()
    ctx = _ctx(queue=fake_queue, sessionmaker=sessionmaker_factory)

    await sweep(ctx)

    assert len(fake_queue.enqueued) == settings.redispatch_limit


async def test_failure_is_skipped(make_delivery, sessionmaker_factory):
    first = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC)
        - timedelta(seconds=settings.redispatch_limit / 2),
    )
    second = await make_delivery(
        status=DeliveryStatus.pending,
        attempt_count=0,
        next_attempt_at=datetime.now(UTC)
        - timedelta(seconds=settings.redispatch_limit / 2),
    )

    fake_raising_queue = FakeRaisingQueue(fail_for={str(first.id)})
    ctx = _ctx(queue=fake_raising_queue, sessionmaker=sessionmaker_factory)
    await sweep(ctx)

    assert len(fake_raising_queue.enqueued) == 1
    assert fake_raising_queue.enqueued[0]["delivery_id"] == str(second.id)
