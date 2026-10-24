"""Fetching, cleaning, filtering, and deduping feed items."""

from conftest import item, rss

import feeds
import filters
from feeds import collect_stories, fetch_feed, find_image
from filters import clean_text, dedupe, is_same_story, is_sponsored, mentions_ai

FEED = "https://example.com/feed"


def story(title: str, summary: str = "", categories: list[str] | None = None) -> dict:
    return {"title": title, "summary": summary, "categories": categories or [], "source": "Test"}


# ---------- cleaning and filters ----------

def test_clean_text_strips_html_entities_and_wordpress_footer():
    raw = "<p>Big&nbsp;news &amp; more</p> The post Big news appeared first on The New Stack."
    assert clean_text(raw) == "Big news & more"


def test_clean_text_caps_summary_length():
    assert len(clean_text("word " * 500)) == filters.MAX_SUMMARY_CHARS


def test_sponsored_post_caught_by_category_alone():
    # MIT Technology Review marks paid posts only with a "sponsored" category.
    assert is_sponsored(story("The Foundations of Scalable AI", categories=["Artificial intelligence", "sponsored"]))


def test_sponsored_post_caught_by_text():
    assert is_sponsored(story("Faster inference", summary="Presented by Acme"))


def test_normal_story_is_not_sponsored():
    assert not is_sponsored(story("OpenAI launches a new model"))


def test_ai_filter_matches_whole_words_only():
    assert mentions_ai(story("Startup ships AI agents for support"))
    assert not mentions_ai(story("Oracle patches security bugs", summary="The company said it will maintain support."))


# ---------- dedupe ----------

def test_same_story_from_two_outlets_is_detected():
    assert is_same_story("Canva releases its first image generation model",
                         "Canva’s first AI image model plans designs before generating them")


def test_different_stories_about_the_same_company_are_kept_apart():
    assert not is_same_story("OpenAI says it will no longer train its AI models on the live internet",
                             "OpenAI's latest AI models are coming to Google Cloud and Microsoft Azure")


def test_known_limit_very_short_headlines_can_merge():
    # Word overlap is weakest on short headlines: two generic shared words can cross 0.3.
    # Documented trade-off; the LLM editor is the second line of defence.
    assert is_same_story("Newest AI chatbot story", "Older AI agents story")


def test_dedupe_keeps_the_first_newest_copy():
    stories = [story("Canva releases its first image generation model"),
               story("Canva’s first AI image model plans designs before generating them"),
               story("Pennsylvania will require labels on AI ads")]
    assert [s["title"] for s in dedupe(stories)] == [stories[0]["title"], stories[2]["title"]]


# ---------- images ----------

def test_image_from_media_content():
    assert find_image({"media_content": [{"url": "https://img/1.jpg", "medium": "image"}]}) == "https://img/1.jpg"


def test_image_from_enclosure_link():
    assert find_image({"links": [{"type": "image/jpeg", "href": "https://img/2.jpg"}]}) == "https://img/2.jpg"


def test_image_from_first_img_tag_in_summary():
    assert find_image({"summary": '<p>Hi</p><img src="https://img/3.png" alt="">'}) == "https://img/3.png"


def test_no_image_returns_none():
    assert find_image({"summary": "<p>No picture here</p>"}) is None


# ---------- fetching ----------

def test_fetch_feed_returns_clean_items_and_drops_sponsored(fake_http):
    fake_http({FEED: rss(
        item("OpenAI launches a model", "https://a.com/1", summary="<b>Big</b> launch"),
        item("Paid post", "https://a.com/2", categories=("sponsored",)),
    )})
    items = fetch_feed(FEED, "Example")
    assert len(items) == 1
    assert items[0]["title"] == "OpenAI launches a model"
    assert items[0]["summary"] == "Big launch"
    assert items[0]["source"] == "Example"
    assert items[0]["published"].tzinfo is not None


def test_fetch_feed_skips_items_without_a_date(fake_http):
    fake_http({FEED: rss("<item><title>No date</title><link>https://a.com/x</link></item>")})
    assert fetch_feed(FEED, "Example") == []


def test_collect_stories_reports_broken_feeds_and_keeps_going(fake_http, monkeypatch):
    monkeypatch.setattr(feeds, "load_feeds", lambda section: [
        {"name": "Good", "url": FEED, "section": "news"},
        {"name": "Broken", "url": "https://broken.example/feed", "section": "news"},
    ])
    fake_http({FEED: rss(item("AI startup raises money", "https://a.com/1"))})
    stories, failed = collect_stories("news", days=1)
    assert [s["title"] for s in stories] == ["AI startup raises money"]
    assert len(failed) == 1 and failed[0].startswith("Broken:")


def test_collect_stories_filters_by_age_sorts_newest_first_and_applies_feed_flags(fake_http, monkeypatch):
    monkeypatch.setattr(feeds, "load_feeds", lambda section: [
        {"name": "Mixed", "url": FEED, "section": "work", "ai_filter": True, "images": False},
    ])
    fake_http({FEED: rss(
        item("Bayer builds an agentic decision engine for crop scientists", "https://a.com/1", hours_ago=10),
        item("Salesforce adds AI chatbots to Slack frontline tools", "https://a.com/2", hours_ago=1,
             extra='<media:content url="https://img/x.jpg" medium="image"/>'),
        item("Quarterly earnings call", "https://a.com/3", hours_ago=2),
        item("Ancient AI story", "https://a.com/4", hours_ago=24 * 9),
    )})
    stories, failed = collect_stories("work", days=3)
    assert [s["title"] for s in stories] == ["Salesforce adds AI chatbots to Slack frontline tools",
                                            "Bayer builds an agentic decision engine for crop scientists"]
    assert all(s["image"] is None for s in stories)  # images: false
    assert isinstance(stories[0]["published"], str)  # ISO text, ready for JSON
    assert failed == []
