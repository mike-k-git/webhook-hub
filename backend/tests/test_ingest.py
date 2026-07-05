from app.deps import get_queue
from app.main import app
from app.models import DeliveryStatus
from tests.fakes import FakeQueue, FakeRaisingQueue


async def test_create_source_hides_secret(client):
    r = await client.post(
        "/sources", json={"name": "stripe-test", "signing_secret": "secret"}
    )
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "stripe-test"
    assert "signing_secret" not in body  # response schema must never leak it


async def test_ingest_then_list(client, source, signed):
    raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")
    r = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r.status_code == 202
    event_id = r.json()["event_id"]

    r = await client.get("/events")
    assert r.status_code == 200
    events = r.json()["items"]
    assert len(events) == 1
    assert events[0]["id"] == event_id
    assert events[0]["event_type"] == "payment.succeeded"


async def test_ingest_unknown_source(client):
    r = await client.post(
        "/ingest/unknown", json={"type": "x"}, headers={"idempotency-key": "k"}
    )

    assert r.status_code == 404


async def _setup_routes(client, source):
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
    dst2 = (
        await client.post(
            "/destinations",
            json={
                "name": "test_dst_2",
                "url": "http://localhost:8000/",
                "signing_secret": "secret_2",
            },
        )
    ).json()["id"]

    await client.post(
        "/routes", json={"source_id": f"{src_id}", "destination_id": f"{dst}"}
    )
    await client.post(
        "/routes", json={"source_id": f"{src_id}", "destination_id": f"{dst2}"}
    )


async def test_ingest_enqueue(client, source, signed):
    await _setup_routes(client, source)
    raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")

    q = FakeQueue()
    app.dependency_overrides[get_queue] = lambda: q
    r = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r.status_code == 202
    event_id = r.json()["event_id"]

    r2 = await client.get(f"/events/{event_id}")
    assert r2.status_code == 200

    event_details = r2.json()
    assert event_details["id"] == event_id
    assert {e["delivery_id"] for e in q.enqueued} == {
        event_details["deliveries"][0]["id"],
        event_details["deliveries"][1]["id"],
    }


async def test_ingest_failed_enqueue(client, source, signed):
    await _setup_routes(client, source)
    raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")

    q = FakeRaisingQueue(fail_for=set(), fail_all=True)
    app.dependency_overrides[get_queue] = lambda: q
    r = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r.status_code == 202
    event_id = r.json()["event_id"]

    r2 = await client.get(f"/events/{event_id}")
    assert r2.status_code == 200

    event_details = r2.json()
    assert event_details["id"] == event_id
    assert event_details["deliveries"][0]["status"] == DeliveryStatus.pending
    assert event_details["deliveries"][1]["status"] == DeliveryStatus.pending
    assert q.enqueued == []


async def test_ingest_no_enqueue_on_duplicate(client, source, signed):
    await _setup_routes(client, source)
    raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")

    q = FakeQueue()
    app.dependency_overrides[get_queue] = lambda: q
    r = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r.status_code == 202
    event_id = r.json()["event_id"]

    r2 = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r2.status_code == 200
    assert event_id == r2.json()["event_id"]

    r3 = await client.get(f"/events/{event_id}")
    assert r3.status_code == 200

    event_details = r3.json()
    assert event_details["id"] == event_id
    assert {e["delivery_id"] for e in q.enqueued} == {
        event_details["deliveries"][0]["id"],
        event_details["deliveries"][1]["id"],
    }
    assert len(q.enqueued) == 2
