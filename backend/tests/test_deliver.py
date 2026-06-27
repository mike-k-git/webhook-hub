import json
from datetime import UTC, datetime
from typing import cast

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Delivery, DeliveryStatus
from app.tasks import WorkerContext, deliver


async def test_successful_delivery(
    make_event, respx_mock, db_session, sessionmaker_factory
):

    event = await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(DeliveryStatus.pending,),
    )

    delivery_id = (
        await db_session.execute(
            select(Delivery.id).where(Delivery.event_id == event.id)
        )
    ).scalar_one()

    respx_mock.route(method="POST", host="t.test").mock(
        return_value=httpx.Response(200, text="ok")
    )

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            cast(
                WorkerContext,
                {"client": worker_client, "sessionmaker": sessionmaker_factory},
            ),
            delivery_id=str(delivery_id),
        )

    async with sessionmaker_factory() as check:
        delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.id == delivery_id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert delivery.status == DeliveryStatus.succeeded
        assert delivery.attempt_count == 1
        assert len(delivery.attempts) == 1
        assert delivery.attempts[0].response_status == 200


async def test_failed_delivery(
    make_event, respx_mock, db_session, sessionmaker_factory
):

    event = await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(DeliveryStatus.pending,),
    )

    delivery_id = (
        await db_session.execute(
            select(Delivery.id).where(Delivery.event_id == event.id)
        )
    ).scalar_one()

    respx_mock.route(method="POST", host="t.test").mock(
        return_value=httpx.Response(500, text="err")
    )

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            cast(
                WorkerContext,
                {"client": worker_client, "sessionmaker": sessionmaker_factory},
            ),
            delivery_id=str(delivery_id),
        )

    async with sessionmaker_factory() as check:
        delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.event_id == event.id)
                .options(selectinload(Delivery.attempts))
            )
        ).scalar_one()

        assert delivery.next_attempt_at > datetime.now(UTC)
        assert delivery.status == DeliveryStatus.failed
        assert delivery.attempt_count == 1
        assert len(delivery.attempts) == 1
        assert delivery.attempts[0].response_status == 500


async def test_timeout_delivery(
    make_event, respx_mock, db_session, sessionmaker_factory
):

    event = await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(DeliveryStatus.pending,),
    )

    delivery_id = (
        await db_session.execute(
            select(Delivery.id).where(Delivery.event_id == event.id)
        )
    ).scalar_one()

    respx_mock.route(method="POST", host="t.test").mock(
        side_effect=httpx.TimeoutException
    )

    async with httpx.AsyncClient() as worker_client:
        await deliver(
            cast(
                WorkerContext,
                {"client": worker_client, "sessionmaker": sessionmaker_factory},
            ),
            delivery_id=str(delivery_id),
        )

    async with sessionmaker_factory() as check:
        delivery = (
            await check.execute(
                select(Delivery)
                .where(Delivery.event_id == event.id)
                .options(
                    selectinload(Delivery.attempts), selectinload(Delivery.destination)
                )
            )
        ).scalar_one()

        assert delivery.next_attempt_at > datetime.now(UTC)
        assert delivery.status == DeliveryStatus.failed
        assert delivery.attempt_count == 1
        assert len(delivery.attempts) == 1
        assert delivery.attempts[0].error is not None

        call = respx_mock.calls[0]
        assert str(call.request.url) == delivery.destination.url
        assert json.loads(call.request.content) == event.payload
