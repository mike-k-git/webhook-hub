import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class DeliveryStatus(str, enum.Enum):
    pending = "pending"
    delivering = "delivering"
    succeeded = "succeeded"
    failed = "failed"
    dead_letter = "dead_letter"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    signing_secret: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    events: Mapped[list["Event"]] = relationship(back_populates="source")


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(Text)
    signing_secret: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "destination_id", name="uq_routes_source_destination"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    destination_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("destinations.id"), index=True
    )
    transform: Mapped[dict | None] = mapped_column(JSONB)
    event_type_filter: Mapped[str | None] = mapped_column(String(255))


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "idempotency_key", name="uq_events_source_idempotency"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str | None] = mapped_column(String(255))
    payload: Mapped[dict] = mapped_column(JSONB)
    headers: Mapped[dict] = mapped_column(JSONB)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    source: Mapped["Source"] = relationship(back_populates="events")
    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="event")


class Delivery(Base):
    __tablename__ = "deliveries"
    __table_args__ = (Index("ix_deliveries_due", "status", "next_attempt_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"), index=True)
    destination_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("destinations.id"), index=True
    )
    status: Mapped[DeliveryStatus] = mapped_column(
        SAEnum(DeliveryStatus, name="delivery_status"), default=DeliveryStatus.pending
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    locked_by: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    event: Mapped["Event"] = relationship(back_populates="deliveries")
    destination: Mapped["Destination"] = relationship()
    attempts: Mapped[list["DeliveryAttempt"]] = relationship(back_populates="delivery")


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    delivery_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deliveries.id"), index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer)
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int] = mapped_column(Integer)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    delivery: Mapped["Delivery"] = relationship(back_populates="attempts")
