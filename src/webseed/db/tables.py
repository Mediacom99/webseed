"""SQLAlchemy ORM models for the webseed database."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Float, Index, String, Text, Boolean, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class BusinessRow(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    place_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), default="")
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    reviews: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(100), default="")
    maps_url: Mapped[str] = mapped_column(Text, default="")
    has_photos: Mapped[bool] = mapped_column(Boolean, default=False)
    photo_paths: Mapped[list[str]] = mapped_column(JSONB, default=list)  # type: ignore[assignment]
    photo_refs: Mapped[list[str]] = mapped_column(JSONB, default=list)  # type: ignore[assignment]
    fallback_unsplash_url: Mapped[str] = mapped_column(Text, default="")
    lead_score: Mapped[int] = mapped_column(Integer, default=0)
    price_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_status: Mapped[str] = mapped_column(String(50), default="OPERATIONAL")
    primary_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    types: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)  # type: ignore[assignment]
    has_opening_hours: Mapped[bool] = mapped_column(Boolean, default=False)
    opening_hours_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepts_credit_cards: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    editorial_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_texts: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)  # type: ignore[assignment]
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="searched")
    error_detail: Mapped[str] = mapped_column(Text, default="")
    vercel_url: Mapped[str] = mapped_column(Text, default="")
    site_screenshot_path: Mapped[str] = mapped_column(Text, default="")
    email_sent_at: Mapped[str] = mapped_column(String(50), default="")
    test_iterations: Mapped[int] = mapped_column(Integer, default=0)
    test_issues: Mapped[list[dict[str, str]]] = mapped_column(JSONB, default=list)  # type: ignore[assignment]
    run_id: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_businesses_status", "status"),
        Index("idx_businesses_place_id", "place_id"),
    )


class SettingRow(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), server_default=func.now())


class EventLogRow(Base):
    __tablename__ = "event_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[str] = mapped_column(String(36), nullable=False)
    place_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    step: Mapped[str | None] = mapped_column(String(32), nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    data: Mapped[dict[str, str]] = mapped_column(JSONB, default=dict)  # type: ignore[assignment]
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), server_default=func.now())

    __table_args__ = (
        Index("idx_event_log_job_id", "job_id"),
        Index("idx_event_log_timestamp", "timestamp"),
    )
