---
name: require-exception-handling
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.py$
  - field: new_text
    operator: regex_match
    pattern: (run_claude_cli|subprocess\.(run|call|check)|requests\.(get|post)|google\.maps|places_client|vercel|gmail|service\.(users|drafts|labels))
  - field: new_text
    operator: not_contains
    pattern: "except"
---

**External service call without visible exception handling.**

All calls to external services (Claude CLI, Google Maps API, Vercel CLI, Gmail API) must be wrapped in appropriate try/except blocks. These services can fail due to network issues, rate limits, auth problems, or timeouts.

Ensure you wrap the call in a try/except that handles the relevant exceptions (e.g., `subprocess.CalledProcessError`, `requests.RequestException`, `google.api_core.exceptions.GoogleAPIError`).
