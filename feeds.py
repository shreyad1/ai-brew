"""Reading sources.yaml and fetching RSS feeds into clean, filtered, deduped stories."""

import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import httpx
import yaml

from filters import clean_text, dedupe, is_sponsored, mentions_ai

SOURCES_FILE = Path(__file__).parent / "sources.yaml"

# Some sites (e.g. Substack) refuse requests that don't say who's asking.
HEADERS = {"User-Agent": "AI-Brew/1.0 (+https://github.com/shreyad1/ai-brew; RSS reader)"}


def load_feeds(section: str) -> list[dict]:
    """Return the feeds from sources.yaml that belong to one newsletter section."""
    config = yaml.safe_load(SOURCES_FILE.read_text())
    return [feed for feed in config["feeds"] if feed["section"] == section]


IMG_TAG = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']")


def find_image(entry: dict) -> str | None:
    """The image the publisher attached to this feed item, if any. Checked before HTML is stripped."""
    for key in ("media_content", "media_thumbnail"):
        for media in entry.get(key) or []:
            if media.get("url") and media.get("medium", "image") == "image":
                return media["url"]
    for link in entry.get("links") or []:
        if link.get("type", "").startswith("image/"):
            return link.get("href")
    html_parts = [entry.get("summary", "")] + [c.get("value", "") for c in entry.get("content") or []]
    match = IMG_TAG.search(" ".join(html_parts))
    return match.group(1) if match else None


def fetch_feed(url: str, name: str) -> list[dict]:
    """Download one RSS feed and return its items as clean dicts."""
    response = httpx.get(url, timeout=10, follow_redirects=True, headers=HEADERS)
    response.raise_for_status()
    feed = feedparser.parse(response.text)

    items = []
    for entry in feed.entries:
        if not entry.get("published_parsed"):
            continue  # no date means we can't tell if it's recent
        published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        item = {
            "title": clean_text(entry.get("title", "")),
            "link": entry.get("link", ""),
            "source": name,
            "published": published,
            "summary": clean_text(entry.get("summary", "")),
            "categories": [tag.get("term", "") for tag in entry.get("tags", [])],
            "image": find_image(entry),
        }
        if not is_sponsored(item):
            items.append(item)
    return items


def collect_stories(section: str, days: int) -> tuple[list[dict], list[str]]:
    """Fetch every feed in a section and return (recent stories newest first, failed feeds)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stories = []
    failed_feeds = []
    for feed in load_feeds(section):
        try:
            items = fetch_feed(feed["url"], feed["name"])
        except Exception as error:
            failed_feeds.append(f"{feed['name']}: {error}")
            continue
        if feed.get("ai_filter"):
            items = [item for item in items if mentions_ai(item)]
        if feed.get("images") is False:
            for item in items:
                item["image"] = None
        stories.extend(item for item in items if item["published"] >= cutoff)

    stories.sort(key=lambda s: s["published"], reverse=True)
    for story in stories:
        story["published"] = story["published"].isoformat()
    return dedupe(stories), failed_feeds
