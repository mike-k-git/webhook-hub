from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db import SessionDep
from app.models import Source
from app.schemas import SourceCreate, SourceRead

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(body: SourceCreate, session: SessionDep) -> Source:
    source = Source(name=body.name, signing_secret=body.signing_secret)
    session.add(source)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="source name already exists"
        ) from exc
    await session.refresh(source)
    return source


@router.get("", response_model=list[SourceRead])
async def list_sources(session: SessionDep) -> list[Source]:
    result = await session.execute(select(Source).order_by(Source.created_at))
    return list(result.scalars().all())
