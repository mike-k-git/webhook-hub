import json


async def test_same_key_twice_is_one_event(client, source, signed):
    raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")

    r1 = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r1.status_code == 202
    r2 = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r2.status_code == 200
    assert r2.json()["event_id"] == r1.json()["event_id"]

    assert len((await client.get("/events")).json()["items"]) == 1


async def test_identical_body_no_key_dedups(client, source, signed):
    raw, headers = signed({"type": "ping"})

    r1 = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    r2 = await client.post(f"/ingest/{source}", content=raw, headers=headers)
    assert r1.status_code == 202
    assert r2.status_code == 200
    assert len((await client.get("/events")).json()["items"]) == 1


async def test_bad_signature_rejected(client, source):
    raw = json.dumps({"type": "x"}).encode()
    r = await client.post(
        f"/ingest/{source}",
        content=raw,
        headers={"X-Webhook-Signature": "bad-sig", "Content-Type": "application/json"},
    )
    assert r.status_code == 401
    assert (await client.get("/events")).json()["items"] == []


async def test_missing_signature_rejected(client, source):
    raw = json.dumps({"type": "x"}).encode()
    r = await client.post(
        f"/ingest/{source}",
        content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 401
    assert (await client.get("/events")).json()["items"] == []
