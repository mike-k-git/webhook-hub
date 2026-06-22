from sqlalchemy import select

from app.models import Delivery, DeliveryAttempt


async def _insert_delivery_attempt(db_session):
    deliveries = (await db_session.execute(select(Delivery))).scalars().all()

    for delivery in deliveries:
        attempt = DeliveryAttempt(
            delivery_id=delivery.id, attempt_number=1, duration_ms=200
        )
        db_session.add(attempt)

    await db_session.commit()


async def test_delivery_and_attempts_in_response(client, source, signed, db_session):
    src_id = (await client.get("/sources")).json()[0]["id"]
    d1 = (
        await client.post("/destinations", json={"name": "d1", "url": "http://a.test"})
    ).json()["id"]

    await client.post("/routes", json={"source_id": src_id, "destination_id": d1})

    raw, headers = signed({"type": "payment.succeeded"}, key="evt_1")
    event_id = (
        await client.post(f"/ingest/{source}", content=raw, headers=headers)
    ).json()["event_id"]

    await _insert_delivery_attempt(db_session)
    event_details = (await client.get(f"/events/{event_id}")).json()
    print(event_details)

    assert event_details["deliveries"][0]["attempts"][0]["attempt_number"] == 1
    assert event_details["deliveries"][0]["attempts"][0]["duration_ms"] == 200
