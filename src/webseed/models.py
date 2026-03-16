"""Domain models — shared data structures for the webseed pipeline."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class PipelineStatus(str, Enum):
    """All valid business statuses in the pipeline."""

    SEARCHED = "searched"
    ENRICHED = "enriched"
    GENERATED = "generated"
    TESTED = "tested"
    DEPLOYED = "deployed"
    EMAIL_QUEUED = "email_queued"
    EMAILED = "emailed"
    OPTED_OUT = "opted_out"
    # Running statuses (set at step start)
    RUNNING_ENRICH = "running_enrich"
    RUNNING_GENERATE = "running_generate"
    RUNNING_TEST = "running_test"
    RUNNING_DEPLOY = "running_deploy"
    RUNNING_EMAIL = "running_email"
    # Error statuses
    ERROR_ENRICH = "error_enrich"
    ERROR_GENERATE = "error_generate"
    ERROR_TEST = "error_test"
    ERROR_DEPLOY = "error_deploy"
    ERROR_EMAIL = "error_email"
    ERROR_RUN = "error_run"


@dataclass
class BusinessData:
    """Core business data — used throughout the pipeline."""

    name: str
    place_id: str
    address: str
    phone: Optional[str]
    rating: float
    reviews: int
    category: str
    maps_url: str
    has_photos: bool
    photo_paths: list[str]
    fallback_unsplash_url: str
    photo_refs: list[str] = field(default_factory=lambda: list[str]())
    # Enrichment fields (all defaulted for backward compat)
    lead_score: int = 0
    price_level: Optional[str] = None
    business_status: str = "OPERATIONAL"
    primary_type: Optional[str] = None
    types: Optional[list[str]] = None
    has_opening_hours: bool = False
    opening_hours_summary: Optional[str] = None
    accepts_credit_cards: Optional[bool] = None
    editorial_summary: Optional[str] = None
    review_texts: Optional[list[str]] = None


@dataclass
class BusinessRecord:
    """Full business record from the database (BusinessData + persistence metadata)."""

    id: str  # UUID v4
    place_id: str
    name: str
    address: str
    phone: Optional[str]
    email: str
    rating: float
    reviews: int
    category: str
    maps_url: str
    has_photos: bool
    photo_paths: list[str]
    photo_refs: list[str]
    fallback_unsplash_url: str
    lead_score: int
    price_level: Optional[str]
    business_status: str
    primary_type: Optional[str]
    types: Optional[list[str]]
    has_opening_hours: bool
    opening_hours_summary: Optional[str]
    accepts_credit_cards: Optional[bool]
    editorial_summary: Optional[str]
    review_texts: Optional[list[str]]
    status: str
    error_detail: str
    vercel_url: str
    site_screenshot_path: str
    email_sent_at: str
    test_iterations: int
    test_issues: list[dict[str, Any]]
    run_id: str
    created_at: str
    updated_at: str

    @staticmethod
    def new_id() -> str:
        """Generate a new UUID v4 string."""
        return str(uuid.uuid4())


@dataclass
class PipelineEvent:
    """Event emitted during pipeline execution for real-time progress tracking."""

    event_type: str  # step_start, step_done, step_error, progress, cost, job_complete
    job_id: str
    step: str  # search, enrich, generate, test, deploy, email
    place_id: str = ""
    message: str = ""
    data: dict[str, Any] = field(default_factory=lambda: dict[str, Any]())
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
