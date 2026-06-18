from sqlalchemy import func, select

from app.models import Delivery


async def _delivery_count(db_session) -> int:
    return (
        await db_session.execute(select(func.count()).select_from(Delivery))
    ).scalar_one()


async def test_fanout_one_delivery_per_route(client, source, signed, db_session):
    src_id = (await client.get("/sources")).json()[0]["id"]
    d1 = (
        await client.post("/destinations", json={"name": "d1", "url": "http://a.test"})
    ).json()["id"]
    d2 = (
        await client.post("/destinations", json={"name": "d2", "url": "http://b.test"})
    ).json()["id"]
    await client.post("/routes", json={"source_id": src_id, "destination_id": d1})
    await client.post("/routes", json={"source_id": src_id, "destination_id": d2})

    raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")
    r = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r.status_code == 202

    assert await _delivery_count(db_session) == 2


async def test_duplicate_event_adds_no_deliveries(client, source, signed, db_session):
    src_id = (await client.get("/sources")).json()[0]["id"]
    d1 = (
        await client.post("destinations", json={"name": "d1", "url": "http://a.test"})
    ).json()["id"]
    await client.post("/routes", json={"source_id": src_id, "destination_id": d1})

    raw, headers = signed({"type": "x"}, key="evt_1")
    await client.post(f"/ingest/{source}", content=raw, headers=headers)
    r2 = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r2.status_code == 200

    assert await _delivery_count(db_session) == 1


async def test_no_routes_no_deliveries(client, source, signed, db_session):
    raw, headers = signed({"type": "x"}, key="evt_1")
    r = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r.status_code == 202
    assert await _delivery_count(db_session) == 0


async def test_duplicate_route_rejected(client, source):
    src_id = (await client.get("/sources")).json()[0]["id"]
    d1 = (
        await client.post("/destinations", json={"name": "d1", "url": "http://a.test"})
    ).json()["id"]
    r1 = await client.post("/routes", json={"source_id": src_id, "destination_id": d1})
    assert r1.status_code == 201
    r2 = await client.post("/routes", json={"source_id": src_id, "destination_id": d1})
    assert r2.status_code == 409


async def test_deactivate_destination(client):
    d = (
        await client.post("/destinations", json={"name": "d", "url": "http://a.test"})
    ).json()
    assert d["active"] is True
    r = await client.patch(f"/destinations/{d['id']}", json={"active": False})
    assert r.status_code == 200
    assert r.json()["active"] is False
