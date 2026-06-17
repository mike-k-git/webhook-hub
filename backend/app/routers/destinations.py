import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.db import SessionDep
from app.models import Destination
from app.schemas import DestinationCreate, DestinationRead, DestinationUpdate

router = APIRouter(prefix="/destinations", tags=["destinations"])


@router.post("", response_model=DestinationRead, status_code=status.HTTP_201_CREATED)
async def create_destinations(
    body: DestinationCreate, session: SessionDep
) -> Destination:
    dest = Destination(
        name=body.name,
        url=body.url,
        signing_secret=body.signing_secret,
        active=body.active,
    )
    session.add(dest)
    await session.commit()
    await session.refresh(dest)
    return dest


@router.get("", response_model=list[DestinationRead])
async def list_destinations(session: SessionDep) -> list[Destination]:
    result = await session.execute(select(Destination).order_by(Destination.created_at))
    return list(result.scalars().all())


@router.patch("/{destination_id}", response_model=DestinationRead)
async def update_destination(
    destination_id: uuid.UUID, body: DestinationUpdate, session: SessionDep
) -> Destination:
    dest = await session.get(Destination, destination_id)
    if dest is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="unknown destination")
    dest.active = body.active
    await session.commit()
    return dest
