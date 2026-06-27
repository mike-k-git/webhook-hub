from contextlib import asynccontextmanager

from fastapi import FastAPI
from saq import Queue

from app.config import settings
from app.routers import config, deliveries, destinations, events, ingest, routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.queue = Queue.from_url(str(settings.redis_dsn))
    try:
        yield
    finally:
        await app.state.queue.disconnect()


app = FastAPI(title="webhook-hub", lifespan=lifespan)

app.include_router(config.router)
app.include_router(ingest.router)
app.include_router(events.router)
app.include_router(destinations.router)
app.include_router(routes.router)
app.include_router(deliveries.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
