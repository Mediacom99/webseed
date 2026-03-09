"""Vercel deployment — deploy a site directory and return the public URL."""

import subprocess


def deploy(site_dir: str, vercel_token: str) -> str:
    """Deploy the directory to Vercel. Returns the public URL."""
    result = subprocess.run(
        ["vercel", "--prod", "--yes", "--token", vercel_token],
        cwd=site_dir,
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Vercel deploy failed: {result.stderr}")

    # The URL is typically the last https:// line in stdout
    lines = result.stdout.strip().split("\n")
    url = next(
        (line for line in reversed(lines) if line.startswith("https://")),
        lines[-1],
    )
    return url.strip()
