import html
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import httpx
import yaml
from mcp.server.mcpserver import MCPServer

mcp = MCPServer("AI Brew")

SOURCES_FILE = Path(__file__).parent / "sources.yaml"


def load_feeds(section: str) -> list[dict]:
    """Return the feeds from sources.yaml that belong to one newsletter section."""
    config = yaml.safe_load(SOURCES_FILE.read_text())
    return [feed for feed in config["feeds"] if feed["section"] == section]


SPONSORED_MARKERS = ["presented by", "sponsored", "partner content", "insights"]


def is_sponsored(item: dict) -> bool:
    """True if the item looks like paid content rather than journalism."""
    text = " ".join([item["title"], item["summary"], *item["categories"]]).lower()
    return any(marker in text for marker in SPONSORED_MARKERS)


AI_PATTERN = re.compile(
    r"\b(AI|artificial intelligence|machine learning|LLMs?|GenAI|generative|agents?|agentic|chatbots?)\b",
    re.IGNORECASE,
)


def mentions_ai(item: dict) -> bool:
    """True if the item's title, summary, or categories mention AI."""
    text = " ".join([item["title"], item["summary"], *item["categories"]])
    return bool(AI_PATTERN.search(text))


UPCOMING_PATTERN = re.compile(
    r"\b(upcoming|coming soon|coming (?:next|this|later)|will (?:launch|release|roll out|ship|debut|arrive)"
    r"|preview|beta|waitlist|conference|summit|keynote|later this (?:week|month|year)|next (?:week|month))\b",
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
    r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.? \d{1,2}(?:, \d{4})?\b"
)

STOP_WORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "its", "is",
    "at", "by", "from", "as", "that", "this", "it", "new", "says", "after", "how",
    "why", "what", "your", "you", "are", "be", "will", "can", "now",
}
SAME_STORY_THRESHOLD = 0.3  # tuned on real headlines, Oct 24 2026


def headline_words(title: str) -> set[str]:
    """Meaningful lowercase words in a headline, without stop words."""
    words = re.findall(r"[a-z0-9]+", title.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 1}


def is_same_story(title_a: str, title_b: str) -> bool:
    """True if two headlines share enough words to be the same news."""
    a, b = headline_words(title_a), headline_words(title_b)
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= SAME_STORY_THRESHOLD


def dedupe(stories: list[dict]) -> list[dict]:
    """Keep the first story of each group of duplicates (input is newest first)."""
    kept: list[dict] = []
    for story in stories:
        if not any(is_same_story(story["title"], k["title"]) for k in kept):
            kept.append(story)
    return kept


# Some sites (e.g. Substack) refuse requests that don't say who's asking.
HEADERS = {"User-Agent": "AI-Brew/1.0 (+https://github.com/shreyad1/ai-brew; RSS reader)"}

MAX_SUMMARY_CHARS = 500  # we only ever use a short summary, never the full article


def clean_text(raw: str) -> str:
    """Strip HTML tags, entities, and WordPress 'The post ... appeared first' footers."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"\s*The post .* appeared first on .*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_SUMMARY_CHARS]


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
        stories.extend(item for item in items if item["published"] >= cutoff)

    stories.sort(key=lambda s: s["published"], reverse=True)
    for story in stories:
        story["published"] = story["published"].isoformat()
    return dedupe(stories), failed_feeds


@mcp.tool()
def get_ai_news(days: int = 1, limit: int = 20) -> dict:
    """Get recent AI news stories from trusted tech news sites
    (TechCrunch, Ars Technica, The Verge, MIT Technology Review).
    Sponsored posts are filtered out.

    Use this for the latest AI headlines: model launches, funding, policy.
    Returns each story's title, source, link, published date, and short summary.

    Args:
        days: How many days back to look (1-7).
        limit: Max number of stories to return (1-30).
    """
    days = max(1, min(days, 7))
    limit = max(1, min(limit, 30))
    stories, failed_feeds = collect_stories("news", days)
    return {"stories": stories[:limit], "failed_feeds": failed_feeds}


@mcp.tool()
def get_company_ai_updates(days: int = 3, company: str | None = None, limit: int = 20) -> dict:
    """Get stories about real companies adopting or building with AI
    (AWS Machine Learning Blog, CIO.com, Salesforce News).

    Use this for "AI at work": customer case studies, enterprise AI rollouts,
    and how businesses use AI tools.

    Args:
        days: How many days back to look (1-14).
        company: Optional company name to filter by, e.g. "Walmart".
        limit: Max number of stories to return (1-30).
    """
    days = max(1, min(days, 14))
    limit = max(1, min(limit, 30))
    stories, failed_feeds = collect_stories("work", days)
    if company:
        name = company.lower()
        stories = [s for s in stories if name in (s["title"] + " " + s["summary"]).lower()]
    return {"stories": stories[:limit], "failed_feeds": failed_feeds}


@mcp.tool()
def get_upcoming(days: int = 7, limit: int = 10) -> dict:
    """Find recent AI stories that announce something still to come:
    launches, betas, waitlists, previews, conferences, and summits.

    Use this for the "Coming up" section. date_mentioned is a date copied
    from the source text, or null if the source does not state one.
    Never guess a date when it is null.

    Args:
        days: How many days back to search recent stories (1-14).
        limit: Max number of items to return (1-30).
    """
    days = max(1, min(days, 14))
    limit = max(1, min(limit, 30))
    news, news_failed = collect_stories("news", days)
    work, work_failed = collect_stories("work", days)

    upcoming = []
    for story in news + work:
        text = f"{story['title']} {story['summary']}"
        if UPCOMING_PATTERN.search(text):
            date = DATE_PATTERN.search(text)
            story["date_mentioned"] = date.group(0) if date else None
            upcoming.append(story)

    return {"items": upcoming[:limit], "failed_feeds": news_failed + work_failed}


@mcp.tool()
def get_dev_updates(days: int = 3, limit: int = 20) -> dict:
    """Get new AI tools, releases, and techniques for software engineers
    (The New Stack, GitHub Blog).

    Use this for "The Builder's Bar": developer tools, coding agents, evals,
    benchmarks, and AI infrastructure news.

    Args:
        days: How many days back to look (1-14).
        limit: Max number of stories to return (1-30).
    """
    days = max(1, min(days, 14))
    limit = max(1, min(limit, 30))
    stories, failed_feeds = collect_stories("builder", days)
    return {"stories": stories[:limit], "failed_feeds": failed_feeds}


@mcp.tool()
def get_long_reads(days: int = 14, limit: int = 10) -> dict:
    """Get recent essays from respected AI newsletters, mostly on Substack
    (The Pragmatic Engineer, Interconnects, Import AI, One Useful Thing, and more).

    Use this for the weekly "Long Read" pick. These are opinion and analysis
    pieces: attribute claims to the author ("X argues..."), never state them as fact.

    Args:
        days: How many days back to look (1-30). Newsletters post weekly, so default is 14.
        limit: Max number of essays to return (1-30).
    """
    days = max(1, min(days, 30))
    limit = max(1, min(limit, 30))
    stories, failed_feeds = collect_stories("longread", days)
    return {"stories": stories[:limit], "failed_feeds": failed_feeds}


if __name__ == "__main__":
    mcp.run()
