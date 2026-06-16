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
    events = r.json()
    assert len(events) == 1
    assert events[0]["id"] == event_id
    assert events[0]["event_type"] == "payment.succeeded"


async def test_ingest_unknown_source(client):
    r = await client.post(
        "/ingest/unknown", json={"type": "x"}, headers={"idempotency-key": "k"}
    )

    assert r.status_code == 404
