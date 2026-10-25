"""Sending: only drafts are created, only the email body is sent, and API errors are reported clearly."""

import json
from pathlib import Path

import httpx
import pytest

import send

ISSUE = json.loads((Path(__file__).parent.parent / "issues" / "sample.json").read_text())


def test_email_body_strips_the_page_wrapper():
    assert send.email_body("<html><head><title>x</title></head><body class='a'>\n<p>Hi</p>\n</body></html>") == "<p>Hi</p>"


def test_subject_uses_the_lead_headline():
    assert send.subject_for(ISSUE) == "☕ Block built a voice AI that sounds eerily human"


def test_create_draft_always_asks_for_a_draft(monkeypatch):
    sent = {}

    def fake_post(url, headers, json, timeout):
        sent.update(url=url, headers=headers, body=json)
        return httpx.Response(201, json={"id": "em_1", "subject": json["subject"]}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    result = send.create_draft(ISSUE, "secret-key")
    assert result["id"] == "em_1"
    assert sent["body"]["status"] == "draft"
    assert sent["headers"]["Authorization"] == "Token secret-key"
    assert "<body" not in sent["body"]["body"] and "Top Stories" in sent["body"]["body"]


def test_api_errors_are_reported_with_the_reason(monkeypatch):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(401, text="Invalid token", request=httpx.Request("POST", send.API)))
    with pytest.raises(RuntimeError, match="401"):
        send.create_draft(ISSUE, "bad-key")
