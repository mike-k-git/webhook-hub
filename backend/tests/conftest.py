import json
import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import Base, get_session
from app.main import app
from app.models import Delivery, Destination, Event, Source
from app.security import sign

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    maker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with maker() as session:
        yield session


@pytest_asyncio.fixture
async def sessionmaker_factory(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(db_engine):
    maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_session():
        async with maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


SECRET = "secret_test"


@pytest.fixture
def signed():
    def _make(
        body: dict, *, secret: str = SECRET, key: str | None = None
    ) -> tuple[bytes, dict]:
        raw = json.dumps(body).encode()
        headers = {
            "X-Webhook-Signature": sign(secret, raw),
            "Content-Type": "application/json",
        }
        if key is not None:
            headers["Idempotency-Key"] = key
        return raw, headers

    return _make


@pytest_asyncio.fixture
async def source(client) -> str:
    await client.post(
        "/sources", json={"name": "stripe-test", "signing_secret": SECRET}
    )
    return "stripe-test"


@pytest_asyncio.fixture
async def make_event(db_session):
    src = Source(name="seed-src", signing_secret="x")
    dst = Destination(name="seed-dst", url="http://t.test/")
    db_session.add_all([src, dst])
    await db_session.flush()
    n = 0

    async def _make_event(*, source_id=None, received_at, statuses=()):
        nonlocal n
        n += 1
        event = Event(
            source_id=source_id or src.id,
            received_at=received_at,
            idempotency_key=f"k{n}",
            payload={},
            headers={},
        )
        db_session.add(event)
        await db_session.flush()
        for s in statuses:
            db_session.add(
                Delivery(
                    event_id=event.id,
                    destination_id=dst.id,
                    status=s,
                    next_attempt_at=received_at,
                )
            )
        await db_session.commit()
        return event

    return _make_event
