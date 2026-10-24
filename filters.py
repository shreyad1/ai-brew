"""Text rules for feed items: cleaning, sponsored and AI detection, upcoming dates, dedupe.

Pure functions with no network access, so they're fast and easy to test.
"""

import html
import re

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


MAX_SUMMARY_CHARS = 500  # we only ever use a short summary, never the full article


def clean_text(raw: str) -> str:
    """Strip HTML tags, entities, and WordPress 'The post ... appeared first' footers."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    text = re.sub(r"\s*The post .* appeared first on .*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_SUMMARY_CHARS]
