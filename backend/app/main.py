from fastapi import FastAPI

app = FastAPI(title="webhook-hub")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
