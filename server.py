"""AI Brew MCP server: tools that give Claude (or any MCP client) fresh AI news and events.

The logic lives in feeds.py, filters.py, and events.py; each tool here clamps its inputs
and shapes the result.
"""

from mcp.server.mcpserver import MCPServer

from events import LUMA_CITIES, US_STATES, fetch_city_events
from feeds import collect_stories
from filters import DATE_PATTERN, UPCOMING_PATTERN

mcp = MCPServer("AI Brew")


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


@mcp.tool()
def get_ai_events(place: str, days_ahead: int = 30) -> dict:
    """Find upcoming in-person and online AI events (meetups, hackathons, talks) near a place.

    Data comes from Luma's public city calendars. Supported: any US state (name or code,
    e.g. "Texas" or "TX") and the Indian cities New Delhi, Mumbai, and Bengaluru.

    Args:
        place: A US state or one of the supported Indian cities.
        days_ahead: How many days ahead to look (1-60).
    """
    days_ahead = max(1, min(days_ahead, 60))
    wanted = place.strip().lower()
    codes = [code for code, (name, _, _) in US_STATES.items() if wanted in (code.lower(), name.lower())]
    cities = [c for c in LUMA_CITIES if (codes and c["region"] == codes[0]) or c["city"].lower() == wanted]
    if not cities:
        return {"events": [], "note": f"No Luma city calendar for {place!r}. Try a US state or New Delhi, Mumbai, Bengaluru."}

    events, failed = [], []
    for city in cities:
        try:
            events += fetch_city_events(city, days_ahead)
        except Exception as error:
            failed.append(f"{city['city']}: {error}")
    return {"events": sorted(events, key=lambda e: e["start"]), "failed_feeds": failed}


if __name__ == "__main__":
    mcp.run()
