"""PostgresStore — PersistencePort implementation backed by PostgreSQL via SQLAlchemy."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import create_engine, select, update, delete, CursorResult
from sqlalchemy.orm import Session, sessionmaker

from webseed.db.tables import BusinessRow, EventLogRow, SettingRow
from webseed.models import BusinessData, BusinessRecord, PipelineStatus


class PostgresStore:
    """PersistencePort implementation using PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url)
        self._session_factory = sessionmaker(bind=self._engine)

    def _session(self) -> Session:
        return self._session_factory()

    # ── helpers ──

    @staticmethod
    def _row_to_record(row: BusinessRow) -> BusinessRecord:
        return BusinessRecord(
            id=str(row.id),
            place_id=row.place_id,
            name=row.name,
            address=row.address or "",
            phone=row.phone,
            email=row.email or "",
            rating=float(row.rating or 0),
            reviews=int(row.reviews or 0),
            category=row.category or "",
            maps_url=row.maps_url or "",
            has_photos=bool(row.has_photos),
            photo_paths=row.photo_paths or [],
            photo_refs=row.photo_refs or [],
            fallback_unsplash_url=row.fallback_unsplash_url or "",
            lead_score=int(row.lead_score or 0),
            price_level=row.price_level,
            business_status=row.business_status or "OPERATIONAL",
            primary_type=row.primary_type,
            types=row.types,
            has_opening_hours=bool(row.has_opening_hours),
            opening_hours_summary=row.opening_hours_summary,
            accepts_credit_cards=row.accepts_credit_cards,
            editorial_summary=row.editorial_summary,
            review_texts=row.review_texts,
            status=row.status,
            error_detail=row.error_detail or "",
            vercel_url=row.vercel_url or "",
            site_screenshot_path=row.site_screenshot_path or "",
            email_sent_at=row.email_sent_at or "",
            test_iterations=int(row.test_iterations or 0),
            test_issues=row.test_issues or [],
            run_id=row.run_id or "",
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
        )

    # ── Business CRUD ──

    def upsert_business(self, biz: BusinessData, run_id: str) -> str:
        now = datetime.now(timezone.utc)
        with self._session() as session:
            existing = session.execute(
                select(BusinessRow).where(BusinessRow.place_id == biz.place_id)
            ).scalar_one_or_none()

            if existing is not None:
                # Update mutable fields only
                existing.rating = biz.rating
                existing.reviews = biz.reviews
                existing.address = biz.address
                existing.phone = biz.phone or ""
                existing.category = biz.category
                existing.maps_url = biz.maps_url
                existing.lead_score = biz.lead_score
                existing.price_level = biz.price_level
                existing.business_status = biz.business_status
                existing.primary_type = biz.primary_type
                existing.types = biz.types  # type: ignore[assignment]
                existing.has_opening_hours = biz.has_opening_hours
                existing.opening_hours_summary = biz.opening_hours_summary
                existing.accepts_credit_cards = biz.accepts_credit_cards
                existing.editorial_summary = biz.editorial_summary
                existing.review_texts = biz.review_texts  # type: ignore[assignment]
                existing.has_photos = biz.has_photos
                existing.photo_paths = biz.photo_paths  # type: ignore[assignment]
                existing.photo_refs = biz.photo_refs  # type: ignore[assignment]
                existing.fallback_unsplash_url = biz.fallback_unsplash_url
                existing.updated_at = now
                session.commit()
                return "updated"

            row = BusinessRow(
                place_id=biz.place_id,
                name=biz.name,
                address=biz.address,
                phone=biz.phone or "",
                rating=biz.rating,
                reviews=biz.reviews,
                category=biz.category,
                maps_url=biz.maps_url,
                has_photos=biz.has_photos,
                photo_paths=biz.photo_paths,  # type: ignore[arg-type]
                photo_refs=biz.photo_refs,  # type: ignore[arg-type]
                fallback_unsplash_url=biz.fallback_unsplash_url,
                lead_score=biz.lead_score,
                price_level=biz.price_level,
                business_status=biz.business_status,
                primary_type=biz.primary_type,
                types=biz.types,  # type: ignore[arg-type]
                has_opening_hours=biz.has_opening_hours,
                opening_hours_summary=biz.opening_hours_summary,
                accepts_credit_cards=biz.accepts_credit_cards,
                editorial_summary=biz.editorial_summary,
                review_texts=biz.review_texts,  # type: ignore[arg-type]
                status="searched",
                run_id=run_id,
                created_at=now,
                updated_at=now,
            )
            session.add(row)
            session.commit()
            return "inserted"

    def find_by_place_id(self, place_id: str) -> BusinessRecord | None:
        with self._session() as session:
            row = session.execute(
                select(BusinessRow).where(BusinessRow.place_id == place_id)
            ).scalar_one_or_none()
            if row is None:
                return None
            return self._row_to_record(row)

    def find_by_name(self, query: str) -> list[BusinessRecord]:
        with self._session() as session:
            rows = session.execute(
                select(BusinessRow).where(BusinessRow.name.ilike(f"%{query}%"))
            ).scalars().all()
            return [self._row_to_record(r) for r in rows]

    def resolve_identifier(self, identifier: str) -> list[BusinessRecord]:
        result = self.find_by_place_id(identifier)
        if result is not None:
            return [result]
        return self.find_by_name(identifier)

    def update_status(self, place_id: str, status: PipelineStatus, extra: dict[str, Any] | None = None) -> bool:
        now = datetime.now(timezone.utc)
        with self._session() as session:
            row = session.execute(
                select(BusinessRow).where(BusinessRow.place_id == place_id)
            ).scalar_one_or_none()
            if row is None:
                return False
            row.status = status.value
            row.updated_at = now
            if extra:
                for key, value in extra.items():
                    if hasattr(row, key):
                        setattr(row, key, value)
            session.commit()
            return True

    def delete_business(self, place_id: str) -> bool:
        with self._session() as session:
            cursor: CursorResult[tuple[()]] = session.execute(  # type: ignore[type-arg]
                delete(BusinessRow).where(BusinessRow.place_id == place_id)
            )
            session.commit()
            return (cursor.rowcount or 0) > 0

    def all_place_ids(self) -> set[str]:
        with self._session() as session:
            rows = session.execute(select(BusinessRow.place_id)).scalars().all()
            return set(rows)

    def get_all_businesses(self, status: str | None = None) -> list[BusinessRecord]:
        with self._session() as session:
            stmt = select(BusinessRow)
            if status is not None:
                stmt = stmt.where(BusinessRow.status == status)
            rows = session.execute(stmt).scalars().all()
            return [self._row_to_record(r) for r in rows]

    # ── Blacklist ──

    def get_blacklisted_place_ids(self) -> set[str]:
        with self._session() as session:
            rows = session.execute(
                select(BusinessRow.place_id).where(BusinessRow.status == "opted_out")
            ).scalars().all()
            return set(rows)

    # ── Settings ──

    def get_setting(self, key: str) -> str | None:
        with self._session() as session:
            row = session.execute(
                select(SettingRow).where(SettingRow.key == key)
            ).scalar_one_or_none()
            if row is None:
                return None
            return row.value

    def upsert_setting(self, key: str, value: str, description: str = "") -> None:
        now = datetime.now(timezone.utc)
        with self._session() as session:
            row = session.execute(
                select(SettingRow).where(SettingRow.key == key)
            ).scalar_one_or_none()
            if row is not None:
                row.value = value
                if description:
                    row.description = description
                row.updated_at = now
            else:
                session.add(SettingRow(key=key, value=value, description=description, updated_at=now))
            session.commit()

    def list_settings(self, prefix: str | None = None) -> list[dict[str, Any]]:
        with self._session() as session:
            stmt = select(SettingRow)
            if prefix is not None:
                stmt = stmt.where(SettingRow.key.like(f"{prefix}.%"))
            rows = session.execute(stmt).scalars().all()
            return [
                {
                    "key": r.key,
                    "value": r.value,
                    "description": r.description or "",
                    "updated_at": r.updated_at.isoformat() if r.updated_at else "",
                }
                for r in rows
            ]

    def delete_setting(self, key: str) -> bool:
        with self._session() as session:
            cursor: CursorResult[tuple[()]] = session.execute(  # type: ignore[type-arg]
                delete(SettingRow).where(SettingRow.key == key)
            )
            session.commit()
            return (cursor.rowcount or 0) > 0

    # ── Crash recovery ──

    def reset_stale_running(self) -> int:
        """Reset all running_* statuses to their corresponding error_* statuses."""
        mapping = {
            "running_enrich": "error_enrich",
            "running_generate": "error_generate",
            "running_test": "error_test",
            "running_deploy": "error_deploy",
            "running_email": "error_email",
        }
        total = 0
        with self._session() as session:
            for running_status, error_status in mapping.items():
                cursor: CursorResult[tuple[()]] = session.execute(  # type: ignore[type-arg]
                    update(BusinessRow)
                    .where(BusinessRow.status == running_status)
                    .values(status=error_status, error_detail="reset after crash", updated_at=datetime.now(timezone.utc))
                )
                total += cursor.rowcount or 0
            session.commit()
        return total

    # ── Event logging ──

    def log_event(self, job_id: str, place_id: str, event_type: str, step: str, message: str, data: dict[str, Any]) -> None:
        with self._session() as session:
            session.add(EventLogRow(
                job_id=job_id,
                place_id=place_id or None,
                event_type=event_type,
                step=step or None,
                message=message,
                data=data,  # type: ignore[arg-type]
            ))
            session.commit()
