"""Send an issue to Buttondown as a DRAFT. A person reviews and sends it from the Buttondown dashboard.

    uv run send.py              # draft the newest issue
    uv run send.py 2026-10-25   # draft one issue

Review mode is the default on purpose: nothing reaches subscribers until someone clicks Send.
"""

import json
import os
import re
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from render import render_email

load_dotenv()

ROOT = Path(__file__).parent
ISSUES_DIR = ROOT / "issues"
API = "https://api.buttondown.com/v1/emails"
API_VERSION = "2026-04-01"
BODY_PATTERN = re.compile(r"<body[^>]*>(.*)</body>", re.S)


def email_body(html: str) -> str:
    """Buttondown wraps the email in its own page, so send only what's inside <body>."""
    match = BODY_PATTERN.search(html)
    return match.group(1).strip() if match else html


def subject_for(issue: dict) -> str:
    lead = (issue.get("big_pour") or [{}])[0].get("headline")
    return f"☕ {lead}" if lead else f"The Daily AI Cup · {issue['date_long']}"


def create_draft(issue: dict, api_key: str) -> dict:
    """POST the issue to Buttondown with status 'draft'. Returns Buttondown's email record."""
    response = httpx.post(
        API,
        headers={"Authorization": f"Token {api_key}", "X-API-Version": API_VERSION},
        json={"subject": subject_for(issue), "body": email_body(render_email(issue)), "status": "draft"},
        timeout=30,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Buttondown refused the draft ({response.status_code}): {response.text[:300]}")
    return response.json()


def newest_issue_date() -> str:
    dates = sorted(p.stem for p in ISSUES_DIR.glob("2*.json") if not p.name.endswith(".sources.json"))
    return dates[-1]


if __name__ == "__main__":
    api_key = os.getenv("BUTTONDOWN_API_KEY", "")
    if not api_key:
        sys.exit("No BUTTONDOWN_API_KEY set, so no draft was created.")
    date = next((a for a in sys.argv[1:] if not a.startswith("-")), None) or newest_issue_date()
    issue = json.loads((ISSUES_DIR / f"{date}.json").read_text())
    draft = create_draft(issue, api_key)
    print(f"Draft created in Buttondown: {draft.get('subject')!r} (id {draft.get('id')}). Review and send it from the dashboard.")
