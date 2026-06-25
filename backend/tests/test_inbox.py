from datetime import datetime

from app.models import DeliveryStatus


async def test_inbox_returns_only_dead_letter_deliveries(client, make_event):
    await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(
            DeliveryStatus.succeeded,
            DeliveryStatus.succeeded,
            DeliveryStatus.dead_letter,
        ),
    )

    await make_event(
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )
    r = (await client.get("/deliveries/dead_letter")).json()

    assert len(r) == 1
    assert r[0]["delivery"]["status"] == "dead_letter"
    assert r[0]["event"]["idempotency_key"] == "k1"


async def test_empty_inbox(client, make_event):
    await make_event(
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
        statuses=(DeliveryStatus.delivering,),
    )
    await make_event(
        statuses=(DeliveryStatus.pending,),
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )
    await make_event(
        statuses=(DeliveryStatus.delivering,),
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )

    r = (await client.get("/deliveries/dead_letter")).json()

    assert len(r) == 0


async def test_inbox_limit(client, make_event):

    await make_event(
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
        statuses=(DeliveryStatus.dead_letter,),
    )
    await make_event(
        statuses=(DeliveryStatus.dead_letter,),
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )
    r = (await client.get("/deliveries/dead_letter?limit=1")).json()

    assert len(r) == 1


async def test_inbox_sort(client, make_event):

    await make_event(
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
        statuses=(DeliveryStatus.dead_letter,),
    )
    await make_event(
        statuses=(DeliveryStatus.dead_letter,),
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )
    r = (await client.get("/deliveries/dead_letter")).json()

    assert len(r) == 2
    assert r[0]["event"]["idempotency_key"] == "k2"
    assert r[1]["event"]["idempotency_key"] == "k1"
