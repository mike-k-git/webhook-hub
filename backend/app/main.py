from fastapi import FastAPI

from app.routers import config, deliveries, destinations, events, ingest, routes

app = FastAPI(title="webhook-hub")

app.include_router(config.router)
app.include_router(ingest.router)
app.include_router(events.router)
app.include_router(destinations.router)
app.include_router(routes.router)
app.include_router(deliveries.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
