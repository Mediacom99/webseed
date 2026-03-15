"""Gmail API email module — generate personalized emails with Claude and create Gmail drafts."""

from __future__ import annotations

import base64
import logging
import os
import re
import sys
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Any

log = logging.getLogger(__name__)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]
from googleapiclient.discovery import build  # type: ignore[import-untyped]

SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]

from webseed.claude_cli import get_timeout, run_claude_cli
from webseed.utils import atomic_write

if TYPE_CHECKING:
    from webseed.maps import BusinessData

def _sender_name() -> str:
    return os.getenv("SENDER_NAME", "Edoardo di WebSeed")

_SUBJECT_RE = re.compile(r"---SUBJECT---\s*(.+?)\s*---SUBJECT---", re.DOTALL)
_BODY_RE = re.compile(r"---BODY_HTML---\s*(.+?)\s*---BODY_HTML---", re.DOTALL)


def authenticate() -> Any:
    """Authenticate with Gmail API via OAuth. Returns the Gmail service object."""
    creds: Credentials | None = None
    credentials_file = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    token_file = os.getenv("GMAIL_TOKEN_FILE", "token.json")

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)  # type: ignore[reportUnknownMemberType]

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:  # type: ignore[reportUnknownMemberType]
            creds.refresh(Request())  # type: ignore[reportUnknownMemberType]
        else:
            if not sys.stdin.isatty():
                raise RuntimeError(
                    "Gmail OAuth requires an interactive terminal for first-time authorization. "
                    f"Run the email step interactively to create {token_file}, then re-run headless."
                )
            flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)  # type: ignore[no-untyped-call]
            creds = flow.run_local_server(port=0)  # type: ignore[no-untyped-call]
        assert creds is not None
        token_json: str = creds.to_json()  # type: ignore[reportUnknownMemberType]
        atomic_write(token_file, token_json)
        os.chmod(token_file, 0o600)

    return build("gmail", "v1", credentials=creds)  # type: ignore[no-untyped-call]


def ensure_label(service: Any, label_name: str) -> str:
    """Get or create a Gmail label. Returns the label ID."""
    results: Any = service.users().labels().list(userId="me").execute()
    labels: list[dict[str, Any]] = results.get("labels", [])

    for label in labels:
        if label["name"] == label_name:
            return str(label["id"])

    # Create label
    label_body: dict[str, str] = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created: Any = service.users().labels().create(userId="me", body=label_body).execute()
    return str(created["id"])


EMAIL_SYSTEM_PROMPT = (
    "Sei un copywriter esperto in comunicazione B2B italiana. "
    "Rispondi usando ESCLUSIVAMENTE i marker ---SUBJECT--- e ---BODY_HTML--- come indicato nel prompt. "
    "NON usare JSON, NON usare markdown, NON aggiungere testo fuori dai marker."
)


def generate_email(
    biz: BusinessData, site_url: str, prompt_template: str, contact_email: str = "",
    model: str = "sonnet",
) -> dict[str, str]:
    """Call Claude to generate a personalized email. Returns {'subject', 'body_html'}."""
    prompt = prompt_template.format(
        name=biz.name,
        category=biz.category.replace("_", " "),
        address=biz.address,
        phone=biz.phone or "Non disponibile",
        rating=biz.rating,
        reviews=biz.reviews,
        site_url=site_url,
        contact_email=contact_email,
    )

    raw_text = run_claude_cli(prompt, system_prompt=EMAIL_SYSTEM_PROMPT, model=model, timeout=get_timeout("CLAUDE_TIMEOUT_EMAIL", 180))

    subject_match = _SUBJECT_RE.search(raw_text)
    body_match = _BODY_RE.search(raw_text)

    if not subject_match or not body_match:
        raise ValueError(
            f"Missing ---SUBJECT--- or ---BODY_HTML--- markers in Claude output. "
            f"Raw (first 500): {raw_text[:500]}"
        )

    return {
        "subject": subject_match.group(1).strip(),
        "body_html": body_match.group(1).strip(),
    }


def create_draft(
    service: Any,
    to_email: str,
    subject: str,
    body_html: str,
    screenshot_path: str,
    label_id: str,
) -> str:
    """Create a Gmail draft with embedded screenshot. Returns the draft ID."""
    msg = MIMEMultipart("related")
    msg["Subject"] = subject
    sender_email = os.getenv("CONTACT_EMAIL", "")
    sender_name = _sender_name()
    if sender_email:
        msg["From"] = f"{sender_name} <{sender_email}>"
    else:
        log.warning("CONTACT_EMAIL not set — From header will have display name only")
        msg["From"] = sender_name
    if to_email:
        msg["To"] = to_email

    # Add screenshot reference to HTML body if screenshot exists
    if screenshot_path and os.path.exists(screenshot_path):
        body_html += (
            '<br><hr style="border:none;border-top:1px solid #eee;margin:20px 0;">'
            '<p style="color:#666;font-size:13px;">Anteprima del sito:</p>'
            '<img src="cid:site_preview" style="max-width:100%;border:1px solid #ddd;'
            'border-radius:8px;" alt="Anteprima sito">'
        )

    html_part = MIMEText(body_html, "html")
    msg.attach(html_part)

    # Attach screenshot as inline image
    if screenshot_path and os.path.exists(screenshot_path):
        with open(screenshot_path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="png")
        img.add_header("Content-ID", "<site_preview>")
        img.add_header("Content-Disposition", "inline", filename="preview.png")
        msg.attach(img)

    # Encode and create draft
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft_body: dict[str, dict[str, str]] = {"message": {"raw": raw}}

    draft: Any = (
        service.users().drafts().create(userId="me", body=draft_body).execute()
    )

    # Apply label to the draft message
    if label_id:
        message_id: str = draft["message"]["id"]
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": [label_id]},
        ).execute()

    return str(draft["id"])
