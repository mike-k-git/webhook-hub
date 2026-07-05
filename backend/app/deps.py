from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from saq import Queue
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal


def get_queue(request: Request) -> Queue:
    return request.app.state.queue


QueueDep = Annotated[Queue, Depends(get_queue)]


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
