"""Vercel deployment — all sites under a single 'webseed' project."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess

from webseed.ports import FileStoragePort
log = logging.getLogger(__name__)


def _find_vercel_binary() -> str:
    """Return the path to the Vercel CLI binary."""
    explicit = os.environ.get("VERCEL_CLI_PATH")
    if explicit:
        if not os.path.isfile(explicit):
            raise RuntimeError(f"VERCEL_CLI_PATH set but file not found: {explicit}")
        return explicit

    found = shutil.which("vercel")
    if found:
        return found

    raise RuntimeError(
        "Vercel CLI not found. Install with: npm i -g vercel\n"
        "Or set VERCEL_CLI_PATH in .env"
    )


def check_vercel_ready() -> str:
    """Verify Vercel CLI is installed and logged in. Returns the binary path."""
    vercel_bin = _find_vercel_binary()
    log.info("Using Vercel CLI: %s", vercel_bin)

    # Check logged in by running `vercel whoami`
    result = subprocess.run(
        [vercel_bin, "whoami"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Vercel CLI not logged in. Run: vercel login\n"
            f"stderr: {result.stderr.strip()}"
        )
    log.info("Vercel logged in as: %s", result.stdout.strip())
    return vercel_bin


def remove_deployment(vercel_bin: str, url: str) -> bool:
    """Remove a single Vercel deployment by URL. Returns True if removed."""
    result = subprocess.run(
        [vercel_bin, "remove", url, "--yes"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        log.debug("Vercel remove failed: %s", result.stderr.strip())
    return result.returncode == 0


def deploy(file_storage: FileStoragePort, name_slug: str, vercel_bin: str) -> str:
    """Deploy to Vercel under the shared 'webseed' project. Returns the unique public deployment URL."""
    site_dir = file_storage.site_dir(name_slug)

    # Write project name into vercel.json
    vercel_json_rel = f"{name_slug}/vercel.json"
    vercel_config: dict[str, object] = {}
    if file_storage.exists(vercel_json_rel):
        try:
            vercel_config = json.loads(file_storage.read_file(vercel_json_rel))
        except json.JSONDecodeError:
            vercel_config = {}
    vercel_config["name"] = os.getenv("VERCEL_PROJECT_NAME", "webseed")
    file_storage.write_file(vercel_json_rel, json.dumps(vercel_config, indent=2) + "\n")

    log.debug("Deploying: %s", site_dir)

    try:
        result = subprocess.run(
            [vercel_bin, "--yes"],
            cwd=site_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Vercel deploy timed out after 120s for {site_dir}")

    if result.returncode != 0:
        raise RuntimeError(f"Vercel deploy failed: {result.stderr}")

    # Extract the public URL from Vercel CLI output.
    url = _extract_url(result.stdout)
    if not url:
        raise RuntimeError(
            f"Could not parse deployment URL from Vercel output:\n{result.stdout}"
        )
    log.info("Deployment URL: %s", url)
    return url


def _extract_url(output: str) -> str | None:
    """Extract the https:// deployment URL from Vercel CLI stdout."""
    for line in reversed(output.strip().splitlines()):
        match = re.search(r"https://[^\s\[\]]+\.vercel\.app", line)
        if match:
            return match.group(0)
    return None
