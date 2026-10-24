"""MCP tools: inputs are clamped to safe ranges and results keep their promises."""

import server

STORIES = [{"title": f"AI story {i}", "summary": "Acme uses AI agents", "link": f"https://a.com/{i}",
            "source": "Test", "published": "2026-10-24T00:00:00+00:00"} for i in range(50)]


def fake_collect(calls):
    def collect(section, days):
        calls.append((section, days))
        return [dict(s) for s in STORIES], []
    return collect


def test_get_ai_news_clamps_days_and_limit(monkeypatch):
    calls = []
    monkeypatch.setattr(server, "collect_stories", fake_collect(calls))
    result = server.get_ai_news(days=999, limit=999)
    assert calls == [("news", 7)]
    assert len(result["stories"]) == 30


def test_get_ai_news_never_returns_less_than_one(monkeypatch):
    monkeypatch.setattr(server, "collect_stories", fake_collect([]))
    assert len(server.get_ai_news(days=-5, limit=0)["stories"]) == 1


def test_company_filter_matches_title_or_summary(monkeypatch):
    stories = [{"title": "Walmart rolls out AI agents", "summary": "", "published": "x"},
               {"title": "Bank tries chatbots", "summary": "Built with Walmart's team", "published": "x"},
               {"title": "Unrelated AI news", "summary": "", "published": "x"}]
    monkeypatch.setattr(server, "collect_stories", lambda section, days: (stories, []))
    result = server.get_company_ai_updates(company="walmart")
    assert [s["title"] for s in result["stories"]] == ["Walmart rolls out AI agents", "Bank tries chatbots"]


def test_get_upcoming_only_copies_dates_stated_in_the_source(monkeypatch):
    stories = [
        {"title": "Claude Duet opens a waitlist", "summary": "Available by waitlist.", "published": "x"},
        {"title": "AI summit returns", "summary": "The conference runs Nov 12 in Austin.", "published": "x"},
        {"title": "Company reports earnings", "summary": "Revenue grew.", "published": "x"},
    ]
    monkeypatch.setattr(server, "collect_stories", lambda section, days: ([dict(s) for s in stories] if section == "news" else [], []))
    items = server.get_upcoming()["items"]
    assert [(i["title"], i["date_mentioned"]) for i in items] == [
        ("Claude Duet opens a waitlist", None),
        ("AI summit returns", "Nov 12"),
    ]


def test_get_ai_events_rejects_unsupported_places_politely():
    result = server.get_ai_events("Atlantis")
    assert result["events"] == [] and "No Luma city calendar" in result["note"]
