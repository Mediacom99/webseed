#!/usr/bin/env python3
"""webseed — Genera e deploya siti per business locali senza website."""

from __future__ import annotations

import argparse
import csv
import glob
import logging
import os
import shutil
from collections import Counter
from datetime import datetime
from typing import Any, TYPE_CHECKING

log = logging.getLogger(__name__)

from dotenv import load_dotenv
from tinydb import TinyDB

from webseed import store

if TYPE_CHECKING:
    from webseed.maps import BusinessData

GMAIL_LABEL_NAME = os.getenv("GMAIL_LABEL_NAME", "webseed-queue")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_id(subcommand: str) -> str:
    return f"{subcommand}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def _doc_to_business_data(doc: dict[str, Any]) -> BusinessData:
    """Reconstruct a BusinessData dataclass from a DB document."""
    from webseed.maps import BusinessData, safe_name

    # Use DB-stored photo_paths as primary source, fall back to filesystem scan
    photo_paths: list[str] = doc.get("photo_paths", [])
    if not photo_paths:
        safe = safe_name(str(doc["name"]))
        img_dir = os.path.join("results", safe, "img")
        if os.path.isdir(img_dir):
            photo_paths = [
                f"img/{f}" for f in sorted(os.listdir(img_dir)) if f.endswith(".jpg")
            ]

    return BusinessData(
        name=str(doc["name"]),
        place_id=str(doc["place_id"]),
        address=str(doc["address"]),
        phone=doc.get("phone") or None,
        rating=float(doc.get("rating", 0)),
        reviews=int(doc.get("reviews", 0)),
        category=str(doc.get("category", "")),
        maps_url=str(doc.get("maps_url", "")),
        has_photos=len(photo_paths) > 0,
        photo_paths=photo_paths,
        fallback_unsplash_url=str(doc.get("fallback_unsplash_url", "")),
    )


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    path = os.path.join(os.path.dirname(__file__) or ".", "prompts", filename)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _require_env(*names: str) -> dict[str, str]:
    """Check that environment variables are set and return them as a dict."""
    vals: dict[str, str] = {}
    missing: list[str] = []
    for name in names:
        val = os.getenv(name)
        if not val:
            missing.append(name)
        else:
            vals[name] = val
    if missing:
        print(f"❌ Variabili d'ambiente mancanti: {', '.join(missing)}")
        print("   Copia .env.example in .env e compila.")
        raise SystemExit(1)
    return vals


def _resolve_one(db: TinyDB, identifier: str) -> dict[str, Any] | None:
    """Resolve a single identifier (place_id or name) to one business doc.
    Returns the doc, or None if not found or ambiguous."""
    matches = store.resolve_identifier(db, identifier)
    if not matches:
        print(f"⚠️  Non trovato: {identifier}")
        return None
    if len(matches) == 1:
        doc = matches[0]
        # Show resolved name when searching by name (not exact place_id match)
        if identifier != str(doc["place_id"]):
            print(f"  → {doc['name']} ({doc['place_id']})")
        return doc
    print(f"⚠️  '{identifier}' è ambiguo — {len(matches)} risultati:")
    for m in matches:
        print(f"     • {m['name']} ({m['place_id']}) [{m.get('status', '?')}]")
    return None


def _resolve_many(db: TinyDB, identifiers: list[str]) -> list[dict[str, Any]]:
    """Resolve a list of identifiers to business docs, skipping ambiguous/missing."""
    results: list[dict[str, Any]] = []
    for identifier in identifiers:
        doc = _resolve_one(db, identifier)
        if doc:
            results.append(doc)
    return results


# ---------------------------------------------------------------------------
# Pipeline subcommands
# ---------------------------------------------------------------------------

def cmd_search(args: argparse.Namespace) -> None:
    """Search Maps for businesses without websites, save to DB."""
    env = _require_env("GOOGLE_MAPS_API_KEY")
    from webseed import maps

    db = store.open_db(args.db)
    blacklist = store.get_full_blacklist(db)
    run = _run_id("search")

    print(f"\n🌱 webseed search")
    print(f"   Query: {args.query} in {args.location}")
    print(f"   Limit: {args.limit} business\n")

    print("🔍 Ricerca business su Maps...")
    businesses = maps.search(
        query=args.query,
        location=args.location,
        limit=args.limit,
        api_key=env["GOOGLE_MAPS_API_KEY"],
        output_dir=args.results_dir,
    )
    print(f"\n✓ Trovati {len(businesses)} business senza sito\n")

    inserted = updated = skipped = 0
    for biz in businesses:
        if biz.place_id in blacklist:
            print(f"  Skip (blacklisted): {biz.name}")
            skipped += 1
            continue

        result = store.upsert_business(db, biz, run)
        if result == "inserted":
            print(f"  ✅ Nuovo: {biz.name}")
            inserted += 1
        else:
            print(f"  🔄 Aggiornato: {biz.name}")
            updated += 1

    print(f"\n📊 {inserted} nuovi, {updated} aggiornati, {skipped} blacklisted")


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate HTML sites for businesses at 'searched' status."""
    from webseed import generator

    db = store.open_db(args.db)

    businesses: list[dict[str, Any]] = []
    for doc in _resolve_many(db, args.place_ids):
        if doc.get("status") != "searched":
            print(f"⚠️  {doc.get('name', doc['place_id'])} — status '{doc.get('status')}', non 'searched'. Usa reset prima.")
        else:
            businesses.append(doc)

    if not businesses:
        print("Nessun business da generare (status 'searched').")
        return

    prompt_template = _load_prompt("site_gen.txt")
    system_prompt = _load_prompt("site_gen_system.txt")

    print(f"\n🤖 Generazione siti per {len(businesses)} business\n")

    for i, doc in enumerate(businesses, 1):
        biz = _doc_to_business_data(doc)
        print(f"[{i}/{len(businesses)}] {biz.name}")

        try:
            site_dir = generator.generate(
                biz, args.results_dir, prompt_template, system_prompt,
                model=args.model,
            )
            store.update_status(db, biz.place_id, "generated")
            print(f"  ✅ {site_dir}")
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrotto dall'utente. I business già completati sono stati salvati.")
            break
        except Exception as e:
            store.update_status(
                db, biz.place_id, "error_generate", {"error_detail": str(e)}
            )
            print(f"  ❌ Error: {e}")

    print("\n✓ Generazione completata.")


def cmd_test(args: argparse.Namespace) -> None:
    """Test: code review + optional Playwright visual test, fix loop."""
    from webseed import tester
    from webseed.maps import safe_name

    db = store.open_db(args.db)

    businesses: list[dict[str, Any]] = []
    for doc in _resolve_many(db, args.place_ids):
        if doc.get("status") != "generated":
            print(f"⚠️  {doc.get('name', doc['place_id'])} — status '{doc.get('status')}', non 'generated'. Usa reset prima.")
        else:
            businesses.append(doc)

    if not businesses:
        print("Nessun business da testare (status 'generated').")
        return

    screenshots_dir = os.path.join(args.results_dir, "screenshots")

    # Load test/fix prompts
    code_review_prompt = _load_prompt("code_review.txt")
    fix_prompt = _load_prompt("fix_html.txt")
    visual_test_prompt: str | None = None
    if args.playwright:
        visual_test_prompt = _load_prompt("visual_test.txt")

    print(f"\n🧪 Test per {len(businesses)} business")
    if args.playwright:
        print("   (code review + Playwright visual test)")
    else:
        print("   (code review)")
    print()

    for i, doc in enumerate(businesses, 1):
        biz_name = str(doc["name"])
        place_id = str(doc["place_id"])
        category = str(doc.get("category", ""))
        safe = safe_name(biz_name)
        site_dir = os.path.join(args.results_dir, safe)
        local_html = os.path.join(os.path.abspath(site_dir), "index.html")
        local_url = f"file://{local_html}"

        print(f"[{i}/{len(businesses)}] {biz_name}")

        try:
            test_passed = False
            iteration = 0
            test_result: dict[str, Any] = {}

            for iteration in range(1, args.max_fix_iterations + 2):
                # Code review (text-only, no browser)
                print(f"  🔍 Code review (iterazione {iteration})...")
                test_result = tester.code_review(
                    site_dir, biz_name, category,
                    code_review_prompt,
                    model=args.test_model,
                )

                if not test_result["ok"]:
                    issues: list[dict[str, Any]] = test_result["issues"]
                    summary = test_result["summary"] or test_result["error"]
                    print(f"  ⚠️ Code review: {summary}")
                    for issue in issues:
                        print(f"     [{issue.get('severity', '?')}] {issue.get('description', '')}")

                    if iteration <= args.max_fix_iterations:
                        print("  🔧 Fixing HTML...")
                        try:
                            tester.fix_html(
                                site_dir, issues, biz_name, category,
                                fix_prompt, model=args.test_model,
                            )
                        except Exception as fix_err:
                            print(f"  ❌ Fix fallito: {fix_err}")
                            break
                        continue
                    else:
                        break

                # Code review passed — optionally run Playwright visual test
                if args.playwright:
                    assert visual_test_prompt is not None
                    print(f"  🧪 Playwright visual test (iterazione {iteration})...")
                    test_result = tester.visual_test(
                        local_url, biz_name, category, safe,
                        screenshots_dir, visual_test_prompt,
                        model=args.test_model,
                    )

                    if not test_result["ok"]:
                        issues = test_result["issues"]
                        summary = test_result["summary"] or test_result["error"]
                        print(f"  ⚠️ Visual test: {summary}")
                        for issue in issues:
                            print(f"     [{issue.get('severity', '?')}] {issue.get('description', '')}")

                        if iteration <= args.max_fix_iterations:
                            print("  🔧 Fixing HTML...")
                            try:
                                tester.fix_html(
                                    site_dir, issues, biz_name, category,
                                    fix_prompt, model=args.test_model,
                                )
                            except Exception as fix_err:
                                print(f"  ❌ Fix fallito: {fix_err}")
                                break
                            continue
                        else:
                            break

                # All tests passed
                store.update_status(db, place_id, "tested", {
                    "test_iterations": iteration,
                })
                print("  ✅ Test superati")
                test_passed = True
                break

            if not test_passed:
                store.update_status(
                    db, place_id, "error_test", {
                        "error_detail": test_result.get("summary") or test_result.get("error", "test failed"),
                        "test_iterations": iteration,
                        "test_issues": test_result.get("issues", []),
                    },
                )
                print(f"  ❌ Test falliti dopo {iteration} iterazioni")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrotto dall'utente. I business già completati sono stati salvati.")
            break
        except Exception as e:
            store.update_status(
                db, place_id, "error_test", {"error_detail": str(e)}
            )
            print(f"  ❌ Error: {e}")

        print()

    print("✓ Test completato.")


def cmd_deploy(args: argparse.Namespace) -> None:
    """Deploy to Vercel production + capture email screenshot."""
    from webseed import deployer
    from webseed import tester
    from webseed.maps import safe_name

    vercel_bin = deployer.check_vercel_ready()

    db = store.open_db(args.db)

    businesses: list[dict[str, Any]] = []
    for doc in _resolve_many(db, args.place_ids):
        if doc.get("status") != "tested":
            print(f"⚠️  {doc.get('name', doc['place_id'])} — status '{doc.get('status')}', non 'tested'. Usa test prima.")
        else:
            businesses.append(doc)

    if not businesses:
        print("Nessun business da deployare (status 'tested').")
        return

    screenshots_dir = os.path.join(args.results_dir, "screenshots")

    print(f"\n🚀 Deploy per {len(businesses)} business\n")

    for i, doc in enumerate(businesses, 1):
        biz_name = str(doc["name"])
        place_id = str(doc["place_id"])
        safe = safe_name(biz_name)
        site_dir = os.path.join(args.results_dir, safe)
        print(f"[{i}/{len(businesses)}] {biz_name}")

        try:
            # 1. Deploy
            print("  📤 Deploy in corso...")
            prod_url = deployer.deploy(site_dir, vercel_bin)
            store.update_status(
                db, place_id, "deployed", {"vercel_url": prod_url}
            )
            print(f"  🔗 {prod_url}")

            # 2. Email screenshot
            print("  📸 Capturing email screenshot...")
            email_screenshot = tester.capture_email_screenshot(
                prod_url, safe, screenshots_dir
            )
            if email_screenshot:
                store.update_status(
                    db, place_id, "deployed",
                    {"site_screenshot_path": email_screenshot},
                )

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrotto dall'utente. I business già completati sono stati salvati.")
            break
        except Exception as e:
            store.update_status(
                db, place_id, "error_deploy", {"error_detail": str(e)}
            )
            print(f"  ❌ Error: {e}")

        print()

    print("✓ Deploy completato.")


def cmd_email(args: argparse.Namespace) -> None:
    """Generate personalized emails and create Gmail drafts."""
    env = _require_env("CONTACT_EMAIL")
    from webseed import emailer

    # Check Gmail credentials file before attempting OAuth
    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    if not os.path.exists(credentials_file):
        print(f"❌ File credenziali Gmail non trovato: {credentials_file}")
        print("   Setup: GCP Console → Enable Gmail API → OAuth consent screen →")
        print("   Credentials → Desktop app → Download credentials.json")
        raise SystemExit(1)

    db = store.open_db(args.db)

    businesses: list[dict[str, Any]] = []
    for doc in _resolve_many(db, args.place_ids):
        if doc.get("status") != "deployed":
            print(f"⚠️  {doc.get('name', doc['place_id'])} — status '{doc.get('status')}', non 'deployed'. Usa deploy prima.")
        else:
            businesses.append(doc)

    if not businesses:
        print("Nessun business da contattare (status 'deployed').")
        return

    contact_email = env["CONTACT_EMAIL"]
    prompt_template = _load_prompt("email_gen.txt")
    gmail_service: Any = emailer.authenticate()
    label_id: str = emailer.ensure_label(gmail_service, GMAIL_LABEL_NAME)

    print(f"\n📧 Creazione email per {len(businesses)} business\n")

    for i, doc in enumerate(businesses, 1):
        biz = _doc_to_business_data(doc)
        print(f"[{i}/{len(businesses)}] {biz.name}")

        try:
            email_data = emailer.generate_email(
                biz,
                str(doc.get("vercel_url", "")),
                prompt_template,
                contact_email=contact_email,
                model=args.model,
            )

            # to_email is empty — Maps doesn't provide emails; user fills in Gmail
            draft_id = emailer.create_draft(
                gmail_service,
                to_email=str(doc.get("email", "")),
                subject=email_data["subject"],
                body_html=email_data["body_html"],
                screenshot_path=str(doc.get("site_screenshot_path", "")),
                label_id=label_id,
            )

            store.update_status(db, biz.place_id, "email_queued")
            print(f"  ✅ Draft creato (ID: {draft_id})")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrotto dall'utente. I business già completati sono stati salvati.")
            break
        except Exception as e:
            store.update_status(
                db, biz.place_id, "error_email", {"error_detail": str(e)}
            )
            print(f"  ❌ Error: {e}")

    print(f"\n✓ Email drafts creati. Controlla Gmail con label '{GMAIL_LABEL_NAME}'.")


def cmd_run(args: argparse.Namespace) -> None:
    """Run the full pipeline (generate → test → deploy → email) for specific businesses."""
    from webseed import deployer, emailer, generator, tester
    from webseed.maps import safe_name

    if args.hard:
        args.model = "opus"
        args.test_model = "opus"
        args.max_fix_iterations = 3
        args.verbose = True
        logging.getLogger().setLevel(logging.DEBUG)
        print("🔥 --hard: model=opus, test-model=opus, max-fix-iterations=3, verbose=on")

    db = store.open_db(args.db)

    # Resolve businesses
    businesses: list[dict[str, Any]] = []
    for doc in _resolve_many(db, args.place_ids):
        status = str(doc.get("status", ""))
        if status not in ("searched", "generated", "tested", "deployed",
                          "error_generate", "error_test", "error_deploy", "error_email"):
            print(f"⚠️  {doc.get('name', doc['place_id'])} — status '{status}', non processabile.")
            continue
        businesses.append(doc)

    if not businesses:
        print("Nessun business da processare.")
        return

    # Preload what we need
    prompt_template = _load_prompt("site_gen.txt")
    system_prompt = _load_prompt("site_gen_system.txt")
    code_review_prompt = _load_prompt("code_review.txt")
    fix_prompt = _load_prompt("fix_html.txt")
    screenshots_dir = os.path.join(args.results_dir, "screenshots")

    # Email setup (lazy — only init if we reach that step)
    email_prompt: str | None = None
    gmail_service: Any = None
    label_id: str | None = None
    contact_email = os.getenv("CONTACT_EMAIL", "")

    vercel_bin: str | None = None  # lazy init

    print(f"\n🚀 Pipeline completa per {len(businesses)} business\n")

    for i, doc in enumerate(businesses, 1):
        biz = _doc_to_business_data(doc)
        place_id = biz.place_id
        safe = safe_name(biz.name)
        site_dir = os.path.join(args.results_dir, safe)
        status = str(doc.get("status", "searched"))

        print(f"{'─' * 60}")
        print(f"[{i}/{len(businesses)}] {biz.name} (status: {status})")
        print(f"{'─' * 60}")

        try:
            # ── GENERATE ──
            if status in ("searched", "error_generate"):
                print("\n  🤖 Generazione sito...")
                generator.generate(
                    biz, args.results_dir, prompt_template, system_prompt,
                    model=args.model,
                )
                store.update_status(db, place_id, "generated")
                status = "generated"
                print("  ✅ Sito generato")

            # ── TEST ──
            if status in ("generated", "error_test"):
                print("\n  🧪 Code review...")
                test_passed = False
                test_result: dict[str, Any] = {}

                for iteration in range(1, args.max_fix_iterations + 2):
                    test_result = tester.code_review(
                        site_dir, biz.name, biz.category,
                        code_review_prompt, model=args.test_model,
                    )

                    if test_result["ok"]:
                        store.update_status(db, place_id, "tested", {
                            "test_iterations": iteration,
                        })
                        status = "tested"
                        print(f"  ✅ Test superati (iterazione {iteration})")
                        test_passed = True
                        break

                    issues: list[dict[str, Any]] = test_result["issues"]
                    summary = test_result["summary"] or test_result["error"]
                    print(f"  ⚠️  {summary}")

                    if iteration <= args.max_fix_iterations:
                        print("  🔧 Fixing...")
                        tester.fix_html(
                            site_dir, issues, biz.name, biz.category,
                            fix_prompt, model=args.test_model,
                        )
                    else:
                        break

                if not test_passed:
                    store.update_status(db, place_id, "error_test", {
                        "error_detail": test_result.get("summary", "test failed"),
                    })
                    print(f"  ❌ Test falliti — skipping deploy/email")
                    continue

            # ── DEPLOY ──
            if status in ("tested", "error_deploy"):
                if vercel_bin is None:
                    vercel_bin = deployer.check_vercel_ready()

                print("\n  📤 Deploy in corso...")
                prod_url = deployer.deploy(site_dir, vercel_bin)
                store.update_status(db, place_id, "deployed", {"vercel_url": prod_url})
                status = "deployed"
                print(f"  🔗 {prod_url}")

                # Email screenshot (non-fatal)
                try:
                    print("  📸 Screenshot per email...")
                    email_screenshot = tester.capture_email_screenshot(
                        prod_url, safe, screenshots_dir
                    )
                    if email_screenshot:
                        store.update_status(db, place_id, "deployed", {
                            "site_screenshot_path": email_screenshot,
                        })
                except Exception as ss_err:
                    print(f"  ⚠️  Screenshot fallito: {ss_err}")

            # ── EMAIL ──
            if status in ("deployed", "error_email") and not args.no_email:
                if not contact_email:
                    print("  ⚠️  CONTACT_EMAIL non impostata, skip email")
                    continue

                credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
                if not os.path.exists(credentials_file):
                    print(f"  ⚠️  {credentials_file} non trovato, skip email")
                    continue

                if gmail_service is None:
                    email_prompt = _load_prompt("email_gen.txt")
                    gmail_service = emailer.authenticate()
                    label_id = emailer.ensure_label(gmail_service, GMAIL_LABEL_NAME)

                print("\n  📧 Generazione email...")
                # Re-read doc to get latest screenshot path
                fresh_doc = store.find_by_place_id(db, place_id)
                if fresh_doc is None:
                    print(f"  ⚠️  Business non trovato nel DB, skip email")
                    continue

                assert email_prompt is not None
                assert label_id is not None
                email_data = emailer.generate_email(
                    biz, str(fresh_doc.get("vercel_url", "")), email_prompt,
                    contact_email=contact_email, model=args.model,
                )
                draft_id = emailer.create_draft(
                    gmail_service,
                    to_email=str(fresh_doc.get("email", "")),
                    subject=email_data["subject"],
                    body_html=email_data["body_html"],
                    screenshot_path=str(fresh_doc.get("site_screenshot_path", "")),
                    label_id=label_id,
                )
                store.update_status(db, place_id, "email_queued")
                print(f"  ✅ Draft creato (ID: {draft_id})")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrotto dall'utente. I business già completati sono stati salvati.")
            break
        except Exception as e:
            print(f"  ❌ Error: {e}")
            # Status already set by the failing step or leave as-is

        print()

    print("✓ Pipeline completata.")


# ---------------------------------------------------------------------------
# Management subcommands
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> None:
    """Show all businesses and their statuses."""
    db = store.open_db(args.db)
    docs = store.get_all_businesses(db)

    if not docs:
        print("Database vuoto.")
        return

    filtered_docs = list(docs)
    if args.filter:
        filtered_docs = [d for d in docs if str(d.get("status", "")).startswith(args.filter)]
        if not filtered_docs:
            print(f"Nessun business con status '{args.filter}*'.")
            return

    # Print table
    print(f"\n{'Nome':<25} {'Status':<20} {'URL':<55} {'Place ID':<30}")
    print("─" * 130)
    for doc in filtered_docs:
        name = str(doc.get("name", ""))[:24]
        status = str(doc.get("status", "?"))
        url: str = str(doc.get("vercel_url") or "—")
        if len(url) > 54:
            url = url[:51] + "..."
        place_id = str(doc.get("place_id", ""))[:29]
        print(f"{name:<25} {status:<20} {url:<55} {place_id:<30}")

    print(f"\nTotale: {len(filtered_docs)} business")


def cmd_show(args: argparse.Namespace) -> None:
    """Show full details for a single business."""
    db = store.open_db(args.db)
    doc = _resolve_one(db, args.place_id)

    if not doc:
        return

    for key, value in doc.items():
        if key.startswith("_"):
            continue
        print(f"  {key}: {value}")


def cmd_stats(args: argparse.Namespace) -> None:
    """Show summary statistics."""
    db = store.open_db(args.db)
    docs = store.get_all_businesses(db)

    if not docs:
        print("Database vuoto.")
        return

    status_counts: Counter[str] = Counter(str(d.get("status", "unknown")) for d in docs)

    print(f"\n📊 webseed stats ({args.db})\n")
    print(f"  Totale: {len(docs)} business\n")
    print(f"  {'Status':<20} {'#':>4}")
    print(f"  {'─' * 24}")
    for status, count in sorted(status_counts.items()):
        print(f"  {status:<20} {count:>4}")

    # Last update
    dates = [str(d.get("updated_at", "")) for d in docs if d.get("updated_at")]
    if dates:
        print(f"\n  Ultimo aggiornamento: {max(dates)[:19]}")


def cmd_blacklist_add(args: argparse.Namespace) -> None:
    """Add place_ids to the blacklist."""
    db = store.open_db(args.db)

    docs = _resolve_many(db, args.place_ids)
    resolved_ids = [str(d["place_id"]) for d in docs]

    if not resolved_ids:
        print("Nessun business da aggiungere alla blacklist.")
        return

    store.add_to_blacklist("blacklist.txt", resolved_ids)

    for pid in resolved_ids:
        store.update_status(db, pid, "opted_out")

    print(f"✅ {len(resolved_ids)} place_id aggiunti alla blacklist.")


def cmd_blacklist_remove(args: argparse.Namespace) -> None:
    """Remove a place_id from the blacklist."""
    db = store.open_db(args.db)
    doc = _resolve_one(db, args.place_id)

    if not doc:
        return

    pid = str(doc["place_id"])
    removed_file = store.remove_from_blacklist("blacklist.txt", pid)

    removed_db = False
    if doc.get("status") == "opted_out":
        store.update_status(db, pid, "searched")
        removed_db = True

    if removed_file or removed_db:
        print(f"✅ Rimosso dalla blacklist: {doc['name']} ({pid})")
    else:
        print(f"Non trovato nella blacklist: {doc['name']} ({pid})")


def cmd_blacklist_list(args: argparse.Namespace) -> None:
    """List all blacklisted place_ids."""
    db = store.open_db(args.db)
    full = store.get_full_blacklist(db)

    if not full:
        print("Blacklist vuota.")
        return

    for pid in sorted(full):
        print(f"  {pid}")
    print(f"\nTotale: {len(full)}")


def cmd_reset(args: argparse.Namespace) -> None:
    """Reset a business's status."""
    db = store.open_db(args.db)
    doc = _resolve_one(db, args.place_id)

    if not doc:
        return

    old_status = str(doc.get("status", "?"))
    store.update_status(db, str(doc["place_id"]), args.to, {"error_detail": ""})
    print(f"✅ {doc['name']}: {old_status} → {args.to}")


def cmd_db_delete(args: argparse.Namespace) -> None:
    """Remove businesses from the DB only (keeps local files and Vercel deployments)."""
    db = store.open_db(args.db)

    if args.all:
        # Resolve --skip identifiers to place_ids
        skip_ids: set[str] = set()
        if args.skip:
            for doc in _resolve_many(db, args.skip):
                skip_ids.add(str(doc["place_id"]))
        docs = store.get_all_businesses(db)
        to_delete = [d for d in docs if str(d["place_id"]) not in skip_ids]
    else:
        to_delete = _resolve_many(db, args.place_ids or [])

    if not to_delete:
        print("Nessun business da rimuovere.")
        return

    for doc in to_delete:
        store.delete_business(db, str(doc["place_id"]))
        print(f"  🗑️  Rimosso dal DB: {doc['name']} ({doc['place_id']})")

    print(f"\n✅ Completato. I file locali in results/ non sono stati toccati.")


def cmd_hard_delete(args: argparse.Namespace) -> None:
    """Hard delete: remove DB entry, local files, and Vercel project."""
    from webseed import deployer
    from webseed.maps import safe_name

    db = store.open_db(args.db)
    to_delete = _resolve_many(db, args.place_ids)

    if not to_delete:
        print("Nessun business da rimuovere.")
        return

    # --- Warning summary ---
    print(f"\n⚠️  HARD DELETE — verranno eliminati {len(to_delete)} business:\n")

    for doc in to_delete:
        name = str(doc["name"])
        place_id = str(doc["place_id"])
        safe = safe_name(name)
        site_dir = os.path.join(args.results_dir, safe)
        vercel_url = str(doc.get("vercel_url", ""))
        has_files = os.path.isdir(site_dir)

        print(f"  🗑️  {name} ({place_id})")
        if vercel_url:
            print(f"     → Vercel deployment: {vercel_url}")
        if has_files:
            print(f"     → File locali: {site_dir}/")
        if args.blacklist:
            print(f"     → DB: mantenuto come blacklisted")
        else:
            print(f"     → DB: entry cancellata")
        print()

    # --- Confirmation ---
    if not args.yes:
        try:
            answer = input("Procedere? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAnnullato.")
            return
        if answer not in ("y", "yes", "si", "sì"):
            print("Annullato.")
            return

    # --- Vercel check (lazy, only if needed) ---
    vercel_bin: str | None = None
    needs_vercel = any(doc.get("vercel_url") for doc in to_delete)
    if needs_vercel:
        try:
            vercel_bin = deployer.check_vercel_ready()
        except RuntimeError as e:
            print(f"⚠️  Vercel CLI non disponibile, skip rimozione progetti: {e}")

    # --- Execute ---
    for doc in to_delete:
        name = str(doc["name"])
        place_id = str(doc["place_id"])
        safe = safe_name(name)
        site_dir = os.path.join(args.results_dir, safe)
        screenshots_dir = os.path.join(args.results_dir, "screenshots")

        # 1. Remove Vercel deployment
        vercel_url = str(doc.get("vercel_url", ""))
        if vercel_url and vercel_bin:
            if deployer.remove_deployment(vercel_bin, vercel_url):
                print(f"  ✅ Vercel deployment rimosso: {vercel_url}")
            else:
                print(f"  ⚠️  Vercel deployment non trovato o già rimosso: {vercel_url}")

        # 2. Remove local files
        if os.path.isdir(site_dir):
            shutil.rmtree(site_dir)
            print(f"  ✅ File rimossi: {site_dir}/")

        # Remove screenshots matching this business
        if os.path.isdir(screenshots_dir):
            for f in glob.glob(os.path.join(screenshots_dir, f"{safe}*")):
                os.remove(f)

        # 3. DB: blacklist or delete
        if args.blacklist:
            store.update_status(db, place_id, "opted_out", {
                "vercel_url": "",
                "site_screenshot_path": "",
                "error_detail": "",
            })
            store.add_to_blacklist("blacklist.txt", [place_id])
            print(f"  ✅ Blacklisted: {name}")
        else:
            store.delete_business(db, place_id)
            print(f"  ✅ Rimosso dal DB: {name}")

    print(f"\n✅ Hard delete completato.")


def cmd_close(args: argparse.Namespace) -> None:
    """Close a client: blacklist + remove Vercel deployment, keep local files."""
    from webseed import deployer

    db = store.open_db(args.db)
    to_close = _resolve_many(db, args.place_ids)

    if not to_close:
        print("Nessun business da chiudere.")
        return

    # --- Summary ---
    print(f"\n🔒 CLOSE — verranno chiusi {len(to_close)} business:\n")

    for doc in to_close:
        name = str(doc["name"])
        place_id = str(doc["place_id"])
        vercel_url = str(doc.get("vercel_url", ""))

        print(f"  🔒 {name} ({place_id})")
        if vercel_url:
            print(f"     → Vercel deployment rimosso: {vercel_url}")
        print(f"     → Status: opted_out (blacklisted)")
        print(f"     → File locali: mantenuti")
        print()

    # --- Confirmation ---
    if not args.yes:
        try:
            answer = input("Procedere? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAnnullato.")
            return
        if answer not in ("y", "yes", "si", "sì"):
            print("Annullato.")
            return

    # --- Vercel check (lazy, only if needed) ---
    vercel_bin: str | None = None
    needs_vercel = any(doc.get("vercel_url") for doc in to_close)
    if needs_vercel:
        try:
            vercel_bin = deployer.check_vercel_ready()
        except RuntimeError as e:
            print(f"⚠️  Vercel CLI non disponibile, skip rimozione deploy: {e}")

    # --- Execute ---
    for doc in to_close:
        name = str(doc["name"])
        place_id = str(doc["place_id"])

        # 1. Remove Vercel deployment
        vercel_url = str(doc.get("vercel_url", ""))
        if vercel_url and vercel_bin:
            if deployer.remove_deployment(vercel_bin, vercel_url):
                print(f"  ✅ Vercel deployment rimosso: {vercel_url}")
            else:
                print(f"  ⚠️  Vercel deployment non trovato o già rimosso: {vercel_url}")

        # 2. Blacklist (DB + file)
        store.update_status(db, place_id, "opted_out", {
            "vercel_url": "",
            "site_screenshot_path": "",
            "error_detail": "",
        })
        store.add_to_blacklist("blacklist.txt", [place_id])
        print(f"  ✅ Blacklisted: {name}")

    print(f"\n✅ Close completato.")


def cmd_export_csv(args: argparse.Namespace) -> None:
    """Export the DB to a CSV file."""
    db = store.open_db(args.db)
    docs = store.get_all_businesses(db)

    if not docs:
        print("Database vuoto.")
        return

    # Use all keys from first doc as fieldnames (exclude TinyDB internals)
    fieldnames = [k for k in docs[0].keys() if not k.startswith("_")]

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for doc in docs:
            writer.writerow({k: v for k, v in doc.items() if not k.startswith("_")})

    print(f"✅ Esportati {len(docs)} business in {args.output}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv()

    # Shared flags available both before and after subcommand
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default="webseed.json", help="Path database TinyDB (default: webseed.json)")
    common.add_argument("--results-dir", default="results", help="Directory output (default: results/)")
    common.add_argument("-v", "--verbose", action="store_true", help="Abilita logging dettagliato (DEBUG)")

    parser = argparse.ArgumentParser(
        description="webseed — pipeline siti per business locali",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # --- Pipeline subcommands ---
    p_search = sub.add_parser("search", help="Cerca business su Google Maps", parents=[common])
    p_search.add_argument("--location", required=True, help='Es: "Milano, Italy"')
    p_search.add_argument("--query", required=True, help='Tipo: "ristorante"')
    p_search.add_argument("--limit", type=int, default=10, help="Max (default: 10)")
    p_search.set_defaults(func=cmd_search)

    p_gen = sub.add_parser("generate", help="Genera siti HTML con Claude", parents=[common])
    p_gen.add_argument("--model", default="sonnet", help="Modello Claude (default: sonnet)")
    p_gen.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_gen.set_defaults(func=cmd_generate)

    p_test = sub.add_parser("test", help="Code review + fix loop (locale)", parents=[common])
    p_test.add_argument("--playwright", action="store_true", help="Abilita visual test con Playwright MCP (oltre al code review)")
    p_test.add_argument(
        "--max-fix-iterations", type=int, default=3,
        help="Max cicli fix-retest (default: 3)",
    )
    p_test.add_argument(
        "--test-model", default="sonnet",
        help="Modello Claude per test (default: sonnet)",
    )
    p_test.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_test.set_defaults(func=cmd_test)

    p_deploy = sub.add_parser("deploy", help="Deploy in produzione su Vercel", parents=[common])
    p_deploy.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_deploy.set_defaults(func=cmd_deploy)

    p_email = sub.add_parser("email", help="Crea draft email in Gmail", parents=[common])
    p_email.add_argument("--model", default="sonnet", help="Modello Claude (default: sonnet)")
    p_email.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_email.set_defaults(func=cmd_email)

    p_run = sub.add_parser("run", help="Pipeline completa: generate → test → deploy → email", parents=[common])
    p_run.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_run.add_argument("--model", default="sonnet", help="Modello Claude per generazione e email (default: sonnet)")
    p_run.add_argument("--test-model", default="sonnet", help="Modello Claude per test (default: sonnet)")
    p_run.add_argument("--max-fix-iterations", type=int, default=3, help="Max cicli fix-retest (default: 3)")
    p_run.add_argument("--no-email", action="store_true", help="Skip step email")
    p_run.add_argument("--hard", action="store_true", help="Deep run: opus models, 3 fix iterations, verbose")
    p_run.set_defaults(func=cmd_run)

    # --- Management subcommands ---
    p_status = sub.add_parser("status", help="Mostra stato business", parents=[common])
    p_status.add_argument("--filter", help="Filtra per prefisso status")
    p_status.set_defaults(func=cmd_status)

    p_show = sub.add_parser("show", help="Dettaglio singolo business", parents=[common])
    p_show.add_argument("place_id", help="Place ID o nome business")
    p_show.set_defaults(func=cmd_show)

    p_stats = sub.add_parser("stats", help="Statistiche riassuntive", parents=[common])
    p_stats.set_defaults(func=cmd_stats)

    p_bl_add = sub.add_parser("blacklist-add", help="Aggiungi alla blacklist", parents=[common])
    p_bl_add.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_bl_add.set_defaults(func=cmd_blacklist_add)

    p_bl_rm = sub.add_parser("blacklist-remove", help="Rimuovi dalla blacklist", parents=[common])
    p_bl_rm.add_argument("place_id", help="Place ID o nome business")
    p_bl_rm.set_defaults(func=cmd_blacklist_remove)

    p_bl_ls = sub.add_parser("blacklist-list", help="Mostra blacklist", parents=[common])
    p_bl_ls.set_defaults(func=cmd_blacklist_list)

    p_reset = sub.add_parser("reset", help="Reset status di un business", parents=[common])
    p_reset.add_argument("place_id", help="Place ID o nome business")
    VALID_STATUSES = [
        "searched", "generated", "tested", "deployed",
        "email_queued", "emailed", "opted_out",
        "error_generate", "error_test", "error_deploy", "error_email",
    ]
    p_reset.add_argument(
        "--to", required=True, choices=VALID_STATUSES,
        help="Nuovo status: %(choices)s",
    )
    p_reset.set_defaults(func=cmd_reset)

    p_del = sub.add_parser("db-delete", help="Rimuovi business dal DB (mantiene file locali e Vercel)", parents=[common])
    p_del.add_argument("place_ids", nargs="*", help="Place ID o nome business")
    p_del.add_argument("--all", action="store_true", help="Rimuovi tutti i business")
    p_del.add_argument("--skip", nargs="+", help="Place ID o nome business da escludere (con --all)")
    p_del.set_defaults(func=cmd_db_delete)

    p_hard_del = sub.add_parser("hard-delete", help="Elimina business: DB + file locali + progetto Vercel", parents=[common])
    p_hard_del.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_hard_del.add_argument("--blacklist", action="store_true", help="Mantieni entry in DB come blacklisted invece di cancellare")
    p_hard_del.add_argument("-y", "--yes", action="store_true", help="Salta conferma")
    p_hard_del.set_defaults(func=cmd_hard_delete)

    p_close = sub.add_parser("close", help="Blacklista business e rimuovi deploy Vercel (mantiene file locali)", parents=[common])
    p_close.add_argument("place_ids", nargs="+", help="Place ID o nome business")
    p_close.add_argument("-y", "--yes", action="store_true", help="Salta conferma")
    p_close.set_defaults(func=cmd_close)

    p_export = sub.add_parser("export-csv", help="Esporta DB in CSV", parents=[common])
    p_export.add_argument("--output", default="results.csv", help="File CSV output")
    p_export.set_defaults(func=cmd_export_csv)

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(name)s %(levelname)s: %(message)s",
    )

    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrotto dall'utente.")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
