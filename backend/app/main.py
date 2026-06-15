from fastapi import FastAPI

from app.routers import config, events, ingest

app = FastAPI(title="webhook-hub")

app.include_router(config.router)
app.include_router(ingest.router)
app.include_router(events.router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
