"""Shared test helpers. Tests never touch the network: HTTP calls are replaced with canned responses."""

import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def rss(*items: str) -> str:
    """Wrap <item> blocks in a minimal RSS document."""
    return f'<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>Test Feed</title>{"".join(items)}</channel></rss>'


def item(title: str, link: str, hours_ago: float = 1, summary: str = "", categories: tuple[str, ...] = (), extra: str = "") -> str:
    """One RSS <item>, published `hours_ago` hours before now."""
    published = format_datetime(datetime.now(timezone.utc) - timedelta(hours=hours_ago))
    cats = "".join(f"<category>{c}</category>" for c in categories)
    return f"<item><title>{title}</title><link>{link}</link><pubDate>{published}</pubDate><description><![CDATA[{summary}]]></description>{cats}{extra}</item>"


@pytest.fixture
def fake_http(monkeypatch):
    """Route httpx.get to canned responses: fake_http({url: text}). Unknown URLs return 500."""
    def install(responses: dict[str, str]):
        def fake_get(url, **kwargs):
            request = httpx.Request("GET", url)
            if url in responses:
                return httpx.Response(200, text=responses[url], request=request)
            return httpx.Response(500, text="server error", request=request)
        monkeypatch.setattr(httpx, "get", fake_get)
    return install
