from datetime import UTC, datetime, timedelta
from typing import cast

import httpx
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.config import settings
from app.main import app
from app.models import Delivery, DeliveryStatus
from app.tasks import (
    DeliveryResult,
    DeliverySnapshot,
    WorkerContext,
    deliver,
    sweep,
)
from tests.fakes import FakeQueue, FakeWorker, send_fn


async def test_retry_loop(client, source, sessionmaker_factory, signed):
    src_id = (await client.get("/sources")).json()[0]["id"]
    dst = (
        await client.post(
            "/destinations",
            json={
                "name": "test_dst",
                "url": "http://localhost:8000/docs/",
                "signing_secret": "secret",
            },
        )
    ).json()["id"]

    await client.post(
        "/routes", json={"source_id": f"{src_id}", "destination_id": f"{dst}"}
    )

    app.state.queue = FakeQueue()

    try:
        raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")
        r = await client.post(f"/ingest/{source}", content=raw, headers=headers)
        assert r.status_code == 202
        event_id = r.json()["event_id"]
        r2 = await client.get(f"/events/{event_id}")
        assert r2.status_code == 200
        event_details = r2.json()

        results: list[DeliveryResult] = [
            DeliveryResult(
                success=False,
                response_status=401,
                response_body="",
                error="error",
                duration_ms=10,
            ),
            DeliveryResult(
                success=True,
                response_status=200,
                response_body="",
                error=None,
                duration_ms=10,
            ),
        ]
        calls: list[DeliverySnapshot] = []

        async with httpx.AsyncClient() as worker_client:
            await deliver(
                cast(
                    WorkerContext,
                    {"client": worker_client, "sessionmaker": sessionmaker_factory},
                ),
                delivery_id=str(event_details["deliveries"][0]["id"]),
                send_fn=send_fn(results, calls),
            )

        async with sessionmaker_factory() as check:
            updated_delivery = (
                await check.execute(
                    select(Delivery)
                    .where(Delivery.id == event_details["deliveries"][0]["id"])
                    .options(selectinload(Delivery.attempts))
                )
            ).scalar_one()

            assert updated_delivery.status == DeliveryStatus.failed
            assert updated_delivery.attempt_count == 1
            assert len(updated_delivery.attempts) == 1
            assert len(calls) == 1
            assert len(results) == 1

        async with sessionmaker_factory() as check:
            await check.execute(
                update(Delivery)
                .values(
                    next_attempt_at=datetime.now(UTC)
                    - timedelta(seconds=settings.lease * 2)
                )
                .where(Delivery.id == event_details["deliveries"][0]["id"])
            )
            await check.commit()

        ctx = cast(
            WorkerContext,
            {
                "worker": FakeWorker(app.state.queue),
                "sessionmaker": sessionmaker_factory,
            },
        )
        await sweep(ctx)

        assert event_details["deliveries"][0]["id"] in {
            e["delivery_id"] for e in app.state.queue.enqueued
        }

        async with httpx.AsyncClient() as worker_client:
            await deliver(
                cast(
                    WorkerContext,
                    {"client": worker_client, "sessionmaker": sessionmaker_factory},
                ),
                delivery_id=str(event_details["deliveries"][0]["id"]),
                send_fn=send_fn(results, calls),
            )

        async with sessionmaker_factory() as check:
            updated_delivery = (
                await check.execute(
                    select(Delivery)
                    .where(Delivery.id == event_details["deliveries"][0]["id"])
                    .options(selectinload(Delivery.attempts))
                )
            ).scalar_one()

            assert updated_delivery.status == DeliveryStatus.succeeded
            assert updated_delivery.attempt_count == 2
            assert len(updated_delivery.attempts) == 2
            assert len(calls) == 2
            assert len(results) == 0
    finally:
        del app.state.queue
