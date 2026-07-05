from datetime import UTC, datetime, timedelta
from typing import cast, override

import httpx
from sqlalchemy import update

from app.models import Delivery
from app.tasks import DeliveryResult, DeliverySnapshot, SendFn, WorkerContext, deliver


class FakeQueue:
    def __init__(self) -> None:
        self.enqueued = []

    async def enqueue(self, name, **kwargs):
        self.enqueued.append(kwargs)


class FakeRaisingQueue(FakeQueue):
    def __init__(self, fail_for: set[str], fail_all: bool = False) -> None:
        super().__init__()
        self.fail_for = fail_for
        self.fail_all = fail_all

    @override
    async def enqueue(self, name, **kwargs):
        if self.fail_all or kwargs["delivery_id"] in self.fail_for:
            raise RuntimeError
        await super().enqueue(name, **kwargs)


def send_fn(results: list[DeliveryResult], calls: list[DeliverySnapshot]) -> SendFn:
    async def _send_fn(
        client: httpx.AsyncClient, snapshot: DeliverySnapshot
    ) -> DeliveryResult:
        calls.append(snapshot)
        return results.pop(0)

    return _send_fn


class FakeWorker:
    def __init__(self, queue) -> None:
        self.queue = queue


def ctx(*, queue=None, client=None, sessionmaker=None) -> WorkerContext:
    worker_context = {}
    if queue is not None:
        worker_context["worker"] = FakeWorker(queue)
    if client is not None:
        worker_context["client"] = client
    if sessionmaker is not None:
        worker_context["sessionmaker"] = sessionmaker
    return cast(WorkerContext, worker_context)


def fail_result() -> DeliveryResult:
    return DeliveryResult(
        success=False,
        response_status=500,
        error=None,
        duration_ms=10,
    )


def ok_result() -> DeliveryResult:
    return DeliveryResult(
        success=True,
        response_status=200,
        response_body="",
        error=None,
        duration_ms=10,
    )


def reclaiming_send(sessionmaker_factory, delivery, a_calls, b_calls):

    async def a_send(
        client: httpx.AsyncClient, snapshot: DeliverySnapshot
    ) -> DeliveryResult:
        a_calls.append(snapshot)
        async with sessionmaker_factory() as s:
            await s.execute(
                update(Delivery)
                .where(Delivery.id == delivery.id)
                .values(locked_until=datetime.now(UTC) - timedelta(seconds=1))
            )
            await s.commit()
        await deliver(
            ctx(client=client, sessionmaker=sessionmaker_factory),
            delivery_id=str(delivery.id),
            send_fn=send_fn([ok_result()], b_calls),
        )

        return fail_result()

    return a_send


def fake_rng(a: float, b: float) -> float:
    return b - a
