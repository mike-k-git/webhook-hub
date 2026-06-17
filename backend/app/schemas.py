import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceCreate(BaseModel):
    name: str
    signing_secret: str


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


class IngestAck(BaseModel):
    event_id: uuid.UUID


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    event_type: str | None = None
    idempotency_key: str
    received_at: datetime


class DestinationCreate(BaseModel):
    name: str
    url: str
    signing_secret: str | None = None
    active: bool = True


class DestinationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    active: bool
    created_at: datetime


class DestinationUpdate(BaseModel):
    active: bool


class RouteCreate(BaseModel):
    source_id: uuid.UUID
    destination_id: uuid.UUID


class RouteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    destination_id: uuid.UUID
