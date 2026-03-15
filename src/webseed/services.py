"""Pipeline orchestration — service functions for all pipeline steps and management."""

from __future__ import annotations

import csv
import io
import logging
import os
from collections import Counter
from datetime import datetime
from typing import Any

from webseed import deployer, emailer, generator, maps, tester
from webseed.maps import safe_name
from webseed.models import BusinessData, BusinessRecord, PipelineEvent, PipelineStatus
from webseed.ports import EventCallback, FileStoragePort, PersistencePort

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_id(subcommand: str) -> str:
    return f"{subcommand}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def _record_to_business_data(rec: BusinessRecord, file_storage: FileStoragePort) -> BusinessData:
    """Reconstruct a BusinessData from a BusinessRecord."""
    photo_paths: list[str] = rec.photo_paths or []
    if not photo_paths:
        safe = safe_name(rec.name)
        photo_dir_path = os.path.join(file_storage.site_dir(safe), "img")
        if os.path.isdir(photo_dir_path):
            photo_paths = [
                f"img/{f}" for f in sorted(os.listdir(photo_dir_path)) if f.endswith(".jpg")
            ]

    return BusinessData(
        name=rec.name,
        place_id=rec.place_id,
        address=rec.address,
        phone=rec.phone,
        rating=rec.rating,
        reviews=rec.reviews,
        category=rec.category,
        maps_url=rec.maps_url,
        has_photos=len(photo_paths) > 0 or bool(rec.photo_refs),
        photo_paths=photo_paths,
        photo_refs=rec.photo_refs or [],
        fallback_unsplash_url=rec.fallback_unsplash_url,
        lead_score=rec.lead_score,
        price_level=rec.price_level,
        business_status=rec.business_status,
        primary_type=rec.primary_type,
        types=rec.types,
        has_opening_hours=rec.has_opening_hours,
        opening_hours_summary=rec.opening_hours_summary,
        accepts_credit_cards=rec.accepts_credit_cards,
        editorial_summary=rec.editorial_summary,
        review_texts=rec.review_texts,
    )


def _emit(on_event: EventCallback | None, event_type: str, job_id: str, step: str,
          place_id: str = "", message: str = "", data: dict[str, Any] | None = None) -> None:
    if on_event is not None:
        on_event(PipelineEvent(
            event_type=event_type,
            job_id=job_id,
            step=step,
            place_id=place_id,
            message=message,
            data=data or {},
        ))


def _get_setting(store: PersistencePort, key: str) -> str:
    """Get a required setting from the store. Raises RuntimeError if missing."""
    value = store.get_setting(key)
    if value is None:
        raise RuntimeError(f"Required setting '{key}' not found in database. Run migrations to seed defaults.")
    return value


def _get_config(store: PersistencePort, key: str, default: str) -> str:
    """Get a config setting with fallback."""
    return store.get_setting(key) or default


# ---------------------------------------------------------------------------
# Pipeline service functions
# ---------------------------------------------------------------------------

def run_search(
    query: str,
    location: str,
    limit: int,
    types: list[str],
    min_score: int,
    grid_size: int,
    store: PersistencePort,
    api_key: str,
    on_event: EventCallback | None = None,
    job_id: str = "",
) -> dict[str, Any]:
    """Search for businesses on Maps, save to DB."""
    _emit(on_event, "step_start", job_id, "search", message=f"Searching {query} in {location}")

    existing_ids = store.all_place_ids()
    blacklist = store.get_blacklisted_place_ids()
    run = _run_id("search")

    try:
        businesses = maps.search(
            query=query,
            location=location,
            limit=limit,
            api_key=api_key,
            types=types,
            min_score=min_score,
            grid_size=grid_size,
            skip_place_ids=existing_ids | blacklist,
            on_event=on_event,
        )
    except Exception as e:
        _emit(on_event, "step_error", job_id, "search", message=str(e))
        raise

    inserted = 0
    skipped = 0
    for biz in businesses:
        if biz.place_id in blacklist:
            skipped += 1
            continue
        store.upsert_business(biz, run)
        inserted += 1

    result = {"inserted": inserted, "skipped": skipped, "total_found": len(businesses)}
    _emit(on_event, "step_done", job_id, "search", message=f"{inserted} new, {skipped} blacklisted", data=result)
    return result


def run_enrich(
    place_ids: list[str],
    store: PersistencePort,
    file_storage: FileStoragePort,
    api_key: str,
    only_media: bool = False,
    on_event: EventCallback | None = None,
    job_id: str = "",
) -> dict[str, Any]:
    """Enrich businesses with Place Details + photo download."""
    _emit(on_event, "step_start", job_id, "enrich", message=f"Enriching {len(place_ids)} businesses")

    results: dict[str, str] = {}
    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue

        if rec.status not in ("searched", "error_enrich"):
            results[pid] = f"skipped (status={rec.status})"
            continue

        store.update_status(pid, PipelineStatus.RUNNING_ENRICH)

        try:
            enriched = maps.enrich_business(
                place_id=pid,
                name=rec.name,
                category=rec.category,
                api_key=api_key,
                file_storage=file_storage,
                only_media=only_media,
                existing_photo_refs=rec.photo_refs or None,
                on_event=on_event,
            )

            if enriched.get("has_website"):
                store.update_status(pid, PipelineStatus.ERROR_ENRICH, {"error_detail": "website found during enrichment"})
                results[pid] = "has_website"
                continue

            store.update_status(pid, PipelineStatus.ENRICHED, enriched)
            results[pid] = "enriched"
            _emit(on_event, "progress", job_id, "enrich", place_id=pid,
                  message=f"Enriched {rec.name}", data={"lead_score": enriched.get("lead_score", 0)})

        except Exception as e:
            store.update_status(pid, PipelineStatus.ERROR_ENRICH, {"error_detail": str(e)})
            results[pid] = f"error: {e}"
            _emit(on_event, "step_error", job_id, "enrich", place_id=pid, message=str(e))

    _emit(on_event, "step_done", job_id, "enrich", message=f"Enrichment complete", data={"results": results})
    return {"results": results}


def run_generate(
    place_ids: list[str],
    store: PersistencePort,
    file_storage: FileStoragePort,
    model: str | None = None,
    on_event: EventCallback | None = None,
    job_id: str = "",
) -> dict[str, Any]:
    """Generate HTML sites for businesses."""
    _emit(on_event, "step_start", job_id, "generate", message=f"Generating sites for {len(place_ids)} businesses")

    effective_model = model or _get_config(store, "config.default_model", "sonnet")
    prompt_template = _get_setting(store, "prompt.site_gen")
    system_prompt = _get_setting(store, "prompt.site_gen_system")
    photos_config = generator.parse_kv(_get_setting(store, "prompt.site_gen_photos"))
    no_photos_config = generator.parse_kv(_get_setting(store, "prompt.site_gen_no_photos"))

    results: dict[str, str] = {}
    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue
        if rec.status != "enriched":
            results[pid] = f"skipped (status={rec.status})"
            continue

        store.update_status(pid, PipelineStatus.RUNNING_GENERATE)
        biz = _record_to_business_data(rec, file_storage)

        try:
            generator.generate(
                biz, file_storage, prompt_template, system_prompt,
                model=effective_model,
                photos_config=photos_config,
                no_photos_config=no_photos_config,
            )
            store.update_status(pid, PipelineStatus.GENERATED)
            results[pid] = "generated"
            _emit(on_event, "progress", job_id, "generate", place_id=pid, message=f"Generated {rec.name}")
        except Exception as e:
            store.update_status(pid, PipelineStatus.ERROR_GENERATE, {"error_detail": str(e)})
            results[pid] = f"error: {e}"
            _emit(on_event, "step_error", job_id, "generate", place_id=pid, message=str(e))

    _emit(on_event, "step_done", job_id, "generate", message="Generation complete", data={"results": results})
    return {"results": results}


def run_test(
    place_ids: list[str],
    store: PersistencePort,
    file_storage: FileStoragePort,
    playwright: bool = False,
    max_fix_iterations: int | None = None,
    model: str | None = None,
    on_event: EventCallback | None = None,
    job_id: str = "",
) -> dict[str, Any]:
    """Test: code review + optional Playwright visual test, fix loop."""
    _emit(on_event, "step_start", job_id, "test", message=f"Testing {len(place_ids)} businesses")

    effective_model = model or _get_config(store, "config.test_model", "sonnet")
    max_iters = max_fix_iterations or int(_get_config(store, "config.max_fix_iterations", "3"))

    code_review_prompt = _get_setting(store, "prompt.code_review")
    code_review_system = _get_setting(store, "prompt.code_review_system")
    fix_prompt = _get_setting(store, "prompt.fix_html")
    fix_system = _get_setting(store, "prompt.fix_html_system")
    visual_test_prompt = _get_setting(store, "prompt.visual_test") if playwright else None
    visual_test_system = _get_setting(store, "prompt.visual_test_system") if playwright else None

    results: dict[str, str] = {}
    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue
        if rec.status != "generated":
            results[pid] = f"skipped (status={rec.status})"
            continue

        store.update_status(pid, PipelineStatus.RUNNING_TEST)
        safe = safe_name(rec.name)

        try:
            test_passed = False
            iteration = 0
            test_result: dict[str, Any] = {}

            for iteration in range(1, max_iters + 1):
                # Code review
                test_result = tester.code_review(
                    file_storage, safe, rec.name, rec.category,
                    code_review_prompt, code_review_system,
                    model=effective_model,
                )

                if not test_result["ok"]:
                    issues: list[dict[str, Any]] = test_result["issues"]
                    if iteration <= max_iters:
                        try:
                            tester.fix_html(
                                file_storage, safe, issues, rec.name, rec.category,
                                fix_prompt, fix_system, model=effective_model,
                            )
                        except Exception:
                            break
                        continue
                    else:
                        break

                # Code review passed — optional Playwright visual test
                if playwright and visual_test_prompt and visual_test_system:
                    local_html = os.path.join(os.path.abspath(file_storage.site_dir(safe)), "index.html")
                    local_url = f"file://{local_html}"

                    test_result = tester.visual_test(
                        local_url, rec.name, rec.category,
                        file_storage, visual_test_prompt, visual_test_system,
                        model=effective_model,
                    )

                    if not test_result["ok"]:
                        issues = test_result["issues"]
                        if iteration <= max_iters:
                            try:
                                tester.fix_html(
                                    file_storage, safe, issues, rec.name, rec.category,
                                    fix_prompt, fix_system, model=effective_model,
                                )
                            except Exception:
                                break
                            continue
                        else:
                            break

                # All tests passed
                store.update_status(pid, PipelineStatus.TESTED, {"test_iterations": iteration})
                test_passed = True
                break

            if not test_passed:
                store.update_status(pid, PipelineStatus.ERROR_TEST, {
                    "error_detail": test_result.get("summary") or test_result.get("error", "test failed"),
                    "test_iterations": iteration,
                    "test_issues": test_result.get("issues", []),
                })
                results[pid] = f"failed after {iteration} iterations"
            else:
                results[pid] = "tested"
                _emit(on_event, "progress", job_id, "test", place_id=pid, message=f"Tested {rec.name}")

        except Exception as e:
            store.update_status(pid, PipelineStatus.ERROR_TEST, {"error_detail": str(e)})
            results[pid] = f"error: {e}"
            _emit(on_event, "step_error", job_id, "test", place_id=pid, message=str(e))

    _emit(on_event, "step_done", job_id, "test", message="Testing complete", data={"results": results})
    return {"results": results}


def run_deploy(
    place_ids: list[str],
    store: PersistencePort,
    file_storage: FileStoragePort,
    on_event: EventCallback | None = None,
    job_id: str = "",
) -> dict[str, Any]:
    """Deploy to Vercel + capture email screenshot."""
    _emit(on_event, "step_start", job_id, "deploy", message=f"Deploying {len(place_ids)} businesses")

    vercel_bin = deployer.check_vercel_ready()

    results: dict[str, str] = {}
    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue
        if rec.status != "tested":
            results[pid] = f"skipped (status={rec.status})"
            continue

        store.update_status(pid, PipelineStatus.RUNNING_DEPLOY)
        safe = safe_name(rec.name)

        try:
            prod_url = deployer.deploy(file_storage, safe, vercel_bin)
            store.update_status(pid, PipelineStatus.DEPLOYED, {"vercel_url": prod_url})

            # Email screenshot (non-fatal)
            try:
                email_screenshot = tester.capture_email_screenshot(prod_url, safe, file_storage)
                if email_screenshot:
                    store.update_status(pid, PipelineStatus.DEPLOYED, {"site_screenshot_path": email_screenshot})
            except Exception as ss_err:
                log.warning("Screenshot failed for %s: %s", rec.name, ss_err)

            results[pid] = prod_url
            _emit(on_event, "progress", job_id, "deploy", place_id=pid,
                  message=f"Deployed {rec.name}", data={"url": prod_url})
        except Exception as e:
            store.update_status(pid, PipelineStatus.ERROR_DEPLOY, {"error_detail": str(e)})
            results[pid] = f"error: {e}"
            _emit(on_event, "step_error", job_id, "deploy", place_id=pid, message=str(e))

    _emit(on_event, "step_done", job_id, "deploy", message="Deploy complete", data={"results": results})
    return {"results": results}


def run_email(
    place_ids: list[str],
    store: PersistencePort,
    file_storage: FileStoragePort,
    model: str | None = None,
    on_event: EventCallback | None = None,
    job_id: str = "",
) -> dict[str, Any]:
    """Generate personalized emails and create Gmail drafts."""
    _emit(on_event, "step_start", job_id, "email", message=f"Emailing {len(place_ids)} businesses")

    effective_model = model or _get_config(store, "config.default_model", "sonnet")
    contact_email = _get_config(store, "config.contact_email", "")
    sender_name = _get_config(store, "config.sender_name", "Edoardo di WebSeed")
    gmail_label = _get_config(store, "config.gmail_label_name", "webseed-queue")
    prompt_template = _get_setting(store, "prompt.email_gen")
    system_prompt = _get_setting(store, "prompt.email_gen_system")

    if not contact_email:
        raise RuntimeError("config.contact_email not set — required for email step")

    gmail_service: Any = emailer.authenticate()
    label_id = emailer.ensure_label(gmail_service, gmail_label)

    results: dict[str, str] = {}
    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue
        if rec.status != "deployed":
            results[pid] = f"skipped (status={rec.status})"
            continue

        store.update_status(pid, PipelineStatus.RUNNING_EMAIL)
        biz = _record_to_business_data(rec, file_storage)

        try:
            email_data = emailer.generate_email(
                biz, rec.vercel_url, prompt_template, system_prompt,
                contact_email=contact_email,
                sender_name=sender_name,
                model=effective_model,
            )

            draft_id = emailer.create_draft(
                gmail_service,
                to_email=rec.email or "",
                subject=email_data["subject"],
                body_html=email_data["body_html"],
                screenshot_path=rec.site_screenshot_path or "",
                label_id=label_id,
                contact_email=contact_email,
                sender_name=sender_name,
            )

            store.update_status(pid, PipelineStatus.EMAIL_QUEUED)
            results[pid] = f"draft:{draft_id}"
            _emit(on_event, "progress", job_id, "email", place_id=pid,
                  message=f"Draft created for {rec.name}", data={"draft_id": draft_id})
        except Exception as e:
            store.update_status(pid, PipelineStatus.ERROR_EMAIL, {"error_detail": str(e)})
            results[pid] = f"error: {e}"
            _emit(on_event, "step_error", job_id, "email", place_id=pid, message=str(e))

    _emit(on_event, "step_done", job_id, "email", message="Email complete", data={"results": results})
    return {"results": results}


def run_pipeline(
    place_ids: list[str],
    store: PersistencePort,
    file_storage: FileStoragePort,
    model: str | None = None,
    test_model: str | None = None,
    max_fix_iterations: int | None = None,
    no_email: bool = False,
    playwright: bool = False,
    on_event: EventCallback | None = None,
    job_id: str = "",
) -> dict[str, Any]:
    """Run the full pipeline (enrich → generate → test → deploy → email) for specified businesses."""
    effective_model = model or _get_config(store, "config.default_model", "sonnet")
    effective_test_model = test_model or _get_config(store, "config.test_model", "sonnet")
    max_iters = max_fix_iterations or int(_get_config(store, "config.max_fix_iterations", "3"))

    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")

    # Preload prompts
    prompt_template = _get_setting(store, "prompt.site_gen")
    system_prompt = _get_setting(store, "prompt.site_gen_system")
    photos_config = generator.parse_kv(_get_setting(store, "prompt.site_gen_photos"))
    no_photos_config = generator.parse_kv(_get_setting(store, "prompt.site_gen_no_photos"))
    code_review_prompt = _get_setting(store, "prompt.code_review")
    code_review_system = _get_setting(store, "prompt.code_review_system")
    fix_prompt = _get_setting(store, "prompt.fix_html")
    fix_system = _get_setting(store, "prompt.fix_html_system")

    # Email setup (lazy)
    email_prompt: str | None = None
    email_sys_prompt: str | None = None
    gmail_service: Any = None
    label_id: str | None = None
    contact_email = _get_config(store, "config.contact_email", "")
    sender_name = _get_config(store, "config.sender_name", "Edoardo di WebSeed")

    vercel_bin: str | None = None  # lazy init

    results: dict[str, str] = {}

    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue

        status = rec.status
        if status not in ("searched", "enriched", "generated", "tested", "deployed",
                          "error_enrich", "error_generate", "error_test", "error_deploy", "error_email",
                          "error_run"):
            results[pid] = f"skipped (status={status})"
            continue

        biz = _record_to_business_data(rec, file_storage)
        safe = safe_name(biz.name)

        try:
            # ── ENRICH ──
            if status in ("searched", "error_enrich"):
                if not api_key:
                    results[pid] = "skipped (no API key)"
                    continue

                store.update_status(pid, PipelineStatus.RUNNING_ENRICH)
                enriched = maps.enrich_business(
                    place_id=pid, name=biz.name, category=biz.category,
                    api_key=api_key, file_storage=file_storage,
                    on_event=on_event,
                )
                if enriched.get("has_website"):
                    store.update_status(pid, PipelineStatus.ERROR_ENRICH, {"error_detail": "website found during enrichment"})
                    results[pid] = "has_website"
                    continue

                store.update_status(pid, PipelineStatus.ENRICHED, enriched)
                status = "enriched"
                # Refresh biz
                fresh = store.find_by_place_id(pid)
                if fresh:
                    biz = _record_to_business_data(fresh, file_storage)
                _emit(on_event, "progress", job_id, "enrich", place_id=pid, message=f"Enriched {biz.name}")

            # ── GENERATE ──
            if status in ("enriched", "error_generate"):
                store.update_status(pid, PipelineStatus.RUNNING_GENERATE)
                generator.generate(
                    biz, file_storage, prompt_template, system_prompt,
                    model=effective_model,
                    photos_config=photos_config,
                    no_photos_config=no_photos_config,
                )
                store.update_status(pid, PipelineStatus.GENERATED)
                status = "generated"
                _emit(on_event, "progress", job_id, "generate", place_id=pid, message=f"Generated {biz.name}")

            # ── TEST ──
            if status in ("generated", "error_test"):
                store.update_status(pid, PipelineStatus.RUNNING_TEST)
                test_passed = False
                test_result: dict[str, Any] = {}

                for iteration in range(1, max_iters + 1):
                    test_result = tester.code_review(
                        file_storage, safe, biz.name, biz.category,
                        code_review_prompt, code_review_system,
                        model=effective_test_model,
                    )

                    if test_result["ok"]:
                        store.update_status(pid, PipelineStatus.TESTED, {"test_iterations": iteration})
                        status = "tested"
                        test_passed = True
                        break

                    issues: list[dict[str, Any]] = test_result["issues"]
                    if iteration <= max_iters:
                        tester.fix_html(
                            file_storage, safe, issues, biz.name, biz.category,
                            fix_prompt, fix_system, model=effective_test_model,
                        )

                if not test_passed:
                    store.update_status(pid, PipelineStatus.ERROR_TEST, {
                        "error_detail": test_result.get("summary", "test failed"),
                    })
                    results[pid] = "test_failed"
                    continue

                _emit(on_event, "progress", job_id, "test", place_id=pid, message=f"Tested {biz.name}")

            # ── DEPLOY ──
            if status in ("tested", "error_deploy"):
                if vercel_bin is None:
                    vercel_bin = deployer.check_vercel_ready()

                store.update_status(pid, PipelineStatus.RUNNING_DEPLOY)
                prod_url = deployer.deploy(file_storage, safe, vercel_bin)
                store.update_status(pid, PipelineStatus.DEPLOYED, {"vercel_url": prod_url})
                status = "deployed"

                # Email screenshot (non-fatal)
                try:
                    email_screenshot = tester.capture_email_screenshot(prod_url, safe, file_storage)
                    if email_screenshot:
                        store.update_status(pid, PipelineStatus.DEPLOYED, {"site_screenshot_path": email_screenshot})
                except Exception as ss_err:
                    log.warning("Screenshot failed: %s", ss_err)

                _emit(on_event, "progress", job_id, "deploy", place_id=pid,
                      message=f"Deployed {biz.name}", data={"url": prod_url})

            # ── EMAIL ──
            if status in ("deployed", "error_email") and not no_email:
                if not contact_email:
                    results[pid] = "skipped (no contact_email)"
                    continue

                if gmail_service is None:
                    email_prompt = _get_setting(store, "prompt.email_gen")
                    email_sys_prompt = _get_setting(store, "prompt.email_gen_system")
                    gmail_service = emailer.authenticate()
                    gmail_label = _get_config(store, "config.gmail_label_name", "webseed-queue")
                    label_id = emailer.ensure_label(gmail_service, gmail_label)

                store.update_status(pid, PipelineStatus.RUNNING_EMAIL)

                fresh = store.find_by_place_id(pid)
                if fresh is None:
                    results[pid] = "not_found_after_deploy"
                    continue

                if email_prompt is None or email_sys_prompt is None:
                    raise RuntimeError("Email prompt templates failed to load")
                if label_id is None:
                    raise RuntimeError("Gmail label ID not initialized")

                email_data = emailer.generate_email(
                    biz, fresh.vercel_url, email_prompt, email_sys_prompt,
                    contact_email=contact_email,
                    sender_name=sender_name,
                    model=effective_model,
                )
                draft_id = emailer.create_draft(
                    gmail_service,
                    to_email=fresh.email or "",
                    subject=email_data["subject"],
                    body_html=email_data["body_html"],
                    screenshot_path=fresh.site_screenshot_path or "",
                    label_id=label_id,
                    contact_email=contact_email,
                    sender_name=sender_name,
                )
                store.update_status(pid, PipelineStatus.EMAIL_QUEUED)
                _emit(on_event, "progress", job_id, "email", place_id=pid,
                      message=f"Draft created for {biz.name}", data={"draft_id": draft_id})

            results[pid] = "complete"

        except Exception as e:
            log.exception("Pipeline error for %s", pid)
            # Set error status based on current step
            current = store.find_by_place_id(pid)
            current_status = current.status if current else ""
            if not current_status.startswith("error_"):
                error_map = {
                    "searched": PipelineStatus.ERROR_ENRICH,
                    "enriched": PipelineStatus.ERROR_GENERATE,
                    "generated": PipelineStatus.ERROR_TEST,
                    "tested": PipelineStatus.ERROR_DEPLOY,
                    "deployed": PipelineStatus.ERROR_EMAIL,
                }
                error_status = error_map.get(status, PipelineStatus.ERROR_RUN)
                store.update_status(pid, error_status, {"error_detail": str(e)})
            results[pid] = f"error: {e}"
            _emit(on_event, "step_error", job_id, "pipeline", place_id=pid, message=str(e))

    _emit(on_event, "job_complete", job_id, "pipeline", message="Pipeline complete", data={"results": results})
    return {"results": results}


# ---------------------------------------------------------------------------
# Management service functions
# ---------------------------------------------------------------------------

def get_business(store: PersistencePort, place_id: str) -> BusinessRecord | None:
    return store.find_by_place_id(place_id)


def list_businesses(store: PersistencePort, status: str | None = None) -> list[BusinessRecord]:
    return store.get_all_businesses(status=status)


def get_stats(store: PersistencePort) -> dict[str, int]:
    docs = store.get_all_businesses()
    counts: Counter[str] = Counter(r.status for r in docs)
    result = dict(sorted(counts.items()))
    result["total"] = len(docs)
    return result


def reset_status(store: PersistencePort, place_id: str, to: PipelineStatus) -> bool:
    return store.update_status(place_id, to, {"error_detail": ""})


def blacklist_add(store: PersistencePort, place_ids: list[str]) -> int:
    count = 0
    for pid in place_ids:
        if store.update_status(pid, PipelineStatus.OPTED_OUT):
            count += 1
    return count


def blacklist_remove(store: PersistencePort, place_id: str) -> bool:
    rec = store.find_by_place_id(place_id)
    if rec and rec.status == "opted_out":
        return store.update_status(place_id, PipelineStatus.SEARCHED)
    return False


def hard_delete(
    store: PersistencePort,
    file_storage: FileStoragePort,
    place_ids: list[str],
    keep_blacklisted: bool = False,
) -> dict[str, str]:
    """Hard delete: remove DB entry, local files, and optionally Vercel deployment."""
    vercel_bin: str | None = None
    results: dict[str, str] = {}

    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue

        safe = safe_name(rec.name)

        # Remove Vercel deployment
        if rec.vercel_url:
            if vercel_bin is None:
                try:
                    vercel_bin = deployer.check_vercel_ready()
                except RuntimeError:
                    vercel_bin = ""
            if vercel_bin:
                deployer.remove_deployment(vercel_bin, rec.vercel_url)

        # Remove local files
        file_storage.delete_dir(safe)

        # Remove screenshots
        for f in file_storage.list_files("screenshots", f"{safe}*"):
            try:
                os.remove(f)
            except OSError:
                pass

        # DB: blacklist or delete
        if keep_blacklisted:
            store.update_status(pid, PipelineStatus.OPTED_OUT, {
                "vercel_url": "", "site_screenshot_path": "", "error_detail": "",
            })
            results[pid] = "blacklisted"
        else:
            store.delete_business(pid)
            results[pid] = "deleted"

    return results


def close_businesses(
    store: PersistencePort,
    place_ids: list[str],
) -> dict[str, str]:
    """Close: blacklist + remove Vercel deployment, keep local files."""
    vercel_bin: str | None = None
    results: dict[str, str] = {}

    for pid in place_ids:
        rec = store.find_by_place_id(pid)
        if rec is None:
            results[pid] = "not_found"
            continue

        # Remove Vercel deployment
        if rec.vercel_url:
            if vercel_bin is None:
                try:
                    vercel_bin = deployer.check_vercel_ready()
                except RuntimeError:
                    vercel_bin = ""
            if vercel_bin:
                deployer.remove_deployment(vercel_bin, rec.vercel_url)

        store.update_status(pid, PipelineStatus.OPTED_OUT, {
            "vercel_url": "", "site_screenshot_path": "", "error_detail": "",
        })
        results[pid] = "closed"

    return results


def export_csv(store: PersistencePort) -> str:
    """Export all businesses to CSV string."""
    records = store.get_all_businesses()
    if not records:
        return ""

    output = io.StringIO()
    fieldnames = [
        "place_id", "name", "address", "phone", "email", "category",
        "rating", "reviews", "lead_score", "status", "vercel_url",
        "maps_url", "error_detail", "created_at", "updated_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for rec in records:
        writer.writerow({
            "place_id": rec.place_id,
            "name": rec.name,
            "address": rec.address,
            "phone": rec.phone or "",
            "email": rec.email,
            "category": rec.category,
            "rating": rec.rating,
            "reviews": rec.reviews,
            "lead_score": rec.lead_score,
            "status": rec.status,
            "vercel_url": rec.vercel_url,
            "maps_url": rec.maps_url,
            "error_detail": rec.error_detail,
            "created_at": rec.created_at,
            "updated_at": rec.updated_at,
        })

    return output.getvalue()
