from datetime import datetime

import pytest
from fastapi import HTTPException

from app.models import DeliveryStatus


async def test_events_list_pagination(client, make_event):
    await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
    )

    await make_event(
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )
    await make_event(
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )

    r = (
        await client.get(
            "/events?limit=2",
        )
    ).json()

    assert r["next_cursor"] is not None
    assert len(r["items"]) == 2

    r2 = (await client.get(f"/events?limit=2&cursor={r['next_cursor']}")).json()

    assert r2["next_cursor"] is None
    assert len(r2["items"]) == 1

    ids1 = {i["id"] for i in r["items"]}
    ids2 = {i["id"] for i in r2["items"]}
    assert ids1.isdisjoint(ids2)
    assert len(ids1 | ids2) == 3

    assert r["items"][0]["received_at"] == "2011-11-03T20:05:23Z"


async def test_events_rollups(client, make_event):
    await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(
            DeliveryStatus.succeeded.value,
            DeliveryStatus.succeeded.value,
            DeliveryStatus.dead_letter.value,
        ),
    )

    await make_event(
        received_at=datetime.fromisoformat("2011-11-03T00:05:23+04:00"),
    )
    r = (await client.get("/events")).json()

    assert r["next_cursor"] is None
    assert len(r["items"]) == 2
    assert r["items"][0]["rollup"]["total"] == 3
    assert (
        r["items"][0]["rollup"]["counts_by_status"][DeliveryStatus.succeeded.value] == 2
    )
    assert (
        r["items"][0]["rollup"]["counts_by_status"][DeliveryStatus.dead_letter.value]
        == 1
    )
    assert r["items"][1]["rollup"]["total"] == 0
    assert r["items"][1]["rollup"]["counts_by_status"] == {}


async def test_filter_source(client, make_event, source):
    src_id = (await client.get("/sources")).json()[0]["id"]

    await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(
            DeliveryStatus.succeeded.value,
            DeliveryStatus.succeeded.value,
            DeliveryStatus.dead_letter.value,
        ),
    )

    await make_event(
        source_id=src_id,
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(
            DeliveryStatus.succeeded.value,
            DeliveryStatus.succeeded.value,
            DeliveryStatus.dead_letter.value,
        ),
    )

    r = (await client.get(f"/events?source={source}")).json()

    assert r["next_cursor"] is None
    assert len(r["items"]) == 1


async def test_filter_delivery_status(client, make_event):
    await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(DeliveryStatus.succeeded.value, DeliveryStatus.delivering.value),
    )

    await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(DeliveryStatus.delivering.value,),
    )

    r = (await client.get(f"/events?status={DeliveryStatus.succeeded.value}")).json()

    print(r)
    assert r["next_cursor"] is None
    assert len(r["items"]) == 1
    assert r["items"][0]["rollup"]["total"] == 2
    assert (
        r["items"][0]["rollup"]["counts_by_status"][DeliveryStatus.succeeded.value] == 1
    )
    assert (
        r["items"][0]["rollup"]["counts_by_status"][DeliveryStatus.delivering.value]
        == 1
    )


async def test_unknown_source(client, make_event):
    await make_event(
        received_at=datetime.fromisoformat("2011-11-04T00:05:23+04:00"),
        statuses=(DeliveryStatus.succeeded.value, DeliveryStatus.delivering.value),
    )

    r = (await client.get("/events?source=test_unknown_source")).json()

    assert r["next_cursor"] is None
    assert len(r["items"]) == 0


async def test_invalid_cursor(client):
    r = await client.get("/events?cursor=fakecursor")
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid cursor"
