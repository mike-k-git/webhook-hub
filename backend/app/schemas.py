import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import DeliveryStatus


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


class AttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempt_number: int
    response_status: int | None = None
    response_body: str | None = None
    error: str | None = None
    duration_ms: int
    attempted_at: datetime


class DeliveryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    destination_id: uuid.UUID
    status: DeliveryStatus
    attempt_count: int
    next_attempt_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    attempts: list[AttemptRead]


class EventDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    event_type: str | None = None
    idempotency_key: str
    received_at: datetime
    payload: dict[str, Any]
    headers: dict[str, str]
    deliveries: list[DeliveryRead]


class RollupRead(BaseModel):
    total: int
    counts_by_status: dict[str, int]


class EventListItem(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    event_type: str | None = None
    idempotency_key: str
    received_at: datetime
    rollup: RollupRead


class EventListResponse(BaseModel):
    items: list[EventListItem]
    next_cursor: str | None = None


class DeliveryInboxItem(BaseModel):
    delivery: DeliveryRead
    event: EventRead
