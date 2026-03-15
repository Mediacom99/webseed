"""Claude Code CLI helper — run claude in non-interactive mode and parse results."""

import json
import logging
import os
import re
import shutil
import subprocess
from typing import Any

log = logging.getLogger(__name__)


def get_timeout(env_var: str, default: int) -> int:
    """Read a timeout value from an environment variable, falling back to *default*."""
    raw = os.environ.get(env_var)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        log.warning("%s=%r is not a valid integer, using default %d", env_var, raw, default)
        return default


def _find_claude_binary() -> str:
    """Return the path to the Claude Code CLI binary."""
    explicit = os.environ.get("CLAUDE_CLI_PATH")
    if explicit:
        if not os.path.isfile(explicit):
            raise RuntimeError(f"CLAUDE_CLI_PATH set but file not found: {explicit}")
        return explicit

    found = shutil.which("claude")
    if found:
        return found

    # Common install locations
    for candidate in [
        os.path.expanduser("~/.local/bin/claude"),
        "/usr/local/bin/claude",
        "/opt/homebrew/bin/claude",
    ]:
        if os.path.isfile(candidate):
            return candidate

    raise RuntimeError(
        "Claude Code CLI not found. "
        "Set CLAUDE_CLI_PATH in .env or install from https://claude.ai/cli"
    )


def run_claude_cli(
    prompt: str,
    system_prompt: str,
    model: str = "sonnet",
    timeout: int = 180,
    use_tools: bool = False,
) -> str:
    """Run ``claude --print`` and return the result text.

    When *use_tools* is False (default), tools are disabled so the model
    returns text only.  Set *use_tools* to True for tasks that need
    Playwright MCP or file access.

    Raises ``RuntimeError`` when the CLI is missing or the command fails.
    """
    claude_bin = _find_claude_binary()
    log.info("Using Claude CLI: %s", claude_bin)

    cmd = [
        claude_bin,
        "--print",
        "--output-format", "json",
        "--no-session-persistence",
        "--model", model,
        "--system-prompt", system_prompt,
    ]

    if use_tools:
        cmd.append("--dangerously-skip-permissions")
    else:
        cmd.extend(["--tools", ""])

    log.debug("Running: %s", " ".join(cmd[:6]) + " ...")
    log.debug("Prompt length: %d chars", len(prompt))

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
    )

    if result.returncode != 0:
        log.error("Claude CLI stderr: %s", result.stderr)
        log.error("Claude CLI stdout (first 500): %s", result.stdout[:500])
        raise RuntimeError(f"Claude CLI failed (exit {result.returncode}): {result.stderr}")

    log.debug("Claude CLI returned %d bytes", len(result.stdout))

    try:
        envelope: dict[str, Any] = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Failed to parse Claude CLI JSON output: {exc}. "
            f"Raw stdout (first 500): {result.stdout[:500]}"
        ) from exc
    result_text = envelope.get("result")
    if result_text is None:
        raise RuntimeError(
            f"Claude CLI response missing 'result' key. "
            f"Keys found: {list(envelope.keys())}. "
            f"Raw output (first 500): {result.stdout[:500]}"
        )
    return str(result_text)


_JSON_RESULT_RE = re.compile(
    r"---JSON_RESULT---\s*(.+?)\s*---JSON_RESULT---",
    re.DOTALL,
)


def extract_json_result(text: str) -> dict[str, Any]:
    """Extract the JSON block between ``---JSON_RESULT---`` markers.

    Returns the parsed dict or raises ``ValueError`` when markers/JSON are
    missing or malformed.
    """
    match = _JSON_RESULT_RE.search(text)
    if not match:
        raise ValueError(
            "No ---JSON_RESULT--- block found in Claude output. "
            f"Raw output (first 500 chars): {text[:500]}"
        )
    result: dict[str, Any] = json.loads(match.group(1))
    return result
