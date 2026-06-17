import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db import SessionDep
from app.models import Destination, Route, Source
from app.schemas import RouteCreate, RouteRead


router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("", response_model=RouteRead, status_code=status.HTTP_201_CREATED)
async def create_route(body: RouteCreate, session: SessionDep) -> Route:
    if await session.get(Source, body.source_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="unknown source")
    if await session.get(Destination, body.destination_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="unknown destination")

    route = Route(source_id=body.source_id, destination_id=body.destination_id)
    session.add(route)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="route already exists"
        ) from exc
    await session.refresh(route)
    return route


@router.get("", response_model=list[RouteRead])
async def list_routes(session: SessionDep) -> list[Route]:
    result = await session.execute(select(Route))
    return list(result.scalars().all())


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(route_id: uuid.UUID, session: SessionDep) -> None:
    route = await session.get(Route, route_id)
    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="unknown route"
        )
    await session.delete(route)
    await session.commit()
