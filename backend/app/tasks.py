import uuid

import httpx
from saq import CronJob, Queue
from saq.types import Context, SettingsDict
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import settings as app_settings
from app.db import AsyncSessionLocal


class WorkerContext(Context):
    client: httpx.AsyncClient
    sessionmaker: async_sessionmaker[AsyncSession]


async def deliver(ctx: WorkerContext, *, delivery_id: str) -> None:
    event_delivery_id = uuid.UUID(delivery_id)
    print(delivery_id)
    async with ctx["sessionmaker"]() as session:
        pass


async def sweep(ctx: WorkerContext) -> None:
    print("sweeper")


async def startup(ctx: WorkerContext) -> None:
    ctx["client"] = httpx.AsyncClient(
        timeout=httpx.Timeout(10.0), follow_redirects=False
    )
    ctx["sessionmaker"] = AsyncSessionLocal


async def shutdown(ctx: WorkerContext) -> None:
    await ctx["client"].aclose()


queue = Queue.from_url(str(app_settings.redis_dsn))

settings: SettingsDict[WorkerContext] = SettingsDict(
    queue=queue,
    functions=[deliver],
    concurrency=10,
    cron_jobs=[CronJob(sweep, cron="* * * * * */5")],
    startup=startup,
    shutdown=shutdown,
)
