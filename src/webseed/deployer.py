"""Vercel deployment — preview, test, and promote to production."""

import json
import logging
import os
import shutil
import subprocess

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


def deploy(site_dir: str, vercel_bin: str, project_name: str = "webseed") -> str:
    """Deploy to Vercel production. Returns the production URL."""
    # Write project name into vercel.json
    vercel_json_path = os.path.join(site_dir, "vercel.json")
    vercel_config = {}
    if os.path.exists(vercel_json_path):
        try:
            with open(vercel_json_path, "r") as f:
                vercel_config = json.load(f)
        except json.JSONDecodeError:
            vercel_config = {}
    vercel_config["name"] = project_name
    with open(vercel_json_path, "w") as f:
        json.dump(vercel_config, f, indent=2)
        f.write("\n")

    log.debug("Deploying: %s (project: %s)", site_dir, project_name)

    result = subprocess.run(
        [vercel_bin, "--prod", "--yes"],
        cwd=site_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Vercel deploy failed: {result.stderr}")

    url = result.stdout.strip().splitlines()[-1].strip()
    log.info("Deployment URL: %s", url)
    return url
