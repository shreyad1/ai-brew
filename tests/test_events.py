"""AI events from Luma's iCal feeds."""

from datetime import datetime, timedelta, timezone

import events


def ics_time(delta: timedelta) -> str:
    return (datetime.now(timezone.utc) + delta).strftime("%Y%m%dT%H%M%SZ")


def ics(*vevents: str) -> str:
    return "BEGIN:VCALENDAR\r\n" + "".join(vevents) + "END:VCALENDAR\r\n"


def vevent(summary: str, start: timedelta, description: str = "", location: str = "Venue, 1 Main St, Seattle, WA") -> str:
    return (f"BEGIN:VEVENT\r\nDTSTART:{ics_time(start)}\r\nSUMMARY:{summary}\r\n"
            f"DESCRIPTION:Get up-to-date information at: https://luma.com/abc\\n\\n{description}\r\n"
            f"LOCATION:{location}\r\nEND:VEVENT\r\n")


SEATTLE = {"id": "discplace-test", "city": "Seattle", "region": "WA", "lat": 47.61, "lon": -122.33}


def test_parse_ics_unfolds_long_lines():
    text = "BEGIN:VEVENT\r\nSUMMARY:AI Builders\r\n  Night\r\nDTSTART:20261101T000000Z\r\nEND:VEVENT\r\n"
    assert events.parse_ics(text) == [{"SUMMARY": "AI Builders Night", "DTSTART": "20261101T000000Z"}]


def test_miles_between_known_cities():
    # Seattle to Portland is roughly 145 miles in a straight line.
    assert 135 <= events.miles_between(47.61, -122.33, 45.52, -122.68) <= 155


def test_only_upcoming_ai_events_are_kept(fake_http):
    url = events.LUMA_ICS.format(place_id=SEATTLE["id"])
    fake_http({url: ics(
        vevent("AI Week Hackathon", timedelta(days=2)),
        vevent("Book club", timedelta(days=3), description="We read novels. One mention of AI."),
        vevent("Deep dive", timedelta(days=4), description="AI agents, AI evals, and AI safety talks."),
        vevent("Old AI meetup", timedelta(days=-3)),
        vevent("Far-future AI summit", timedelta(days=90)),
    )})
    found = events.fetch_city_events(SEATTLE, days_ahead=30)
    assert [e["title"] for e in found] == ["AI Week Hackathon", "Deep dive"]
    assert found[0]["link"] == "https://luma.com/abc"
    assert found[0]["venue"] == "Venue"


def test_hidden_address_is_labelled_not_called_online(fake_http):
    url = events.LUMA_ICS.format(place_id=SEATTLE["id"])
    fake_http({url: ics(vevent("AI night", timedelta(days=1), location="https://luma.com/event/evt-1"))})
    assert events.fetch_city_events(SEATTLE)[0]["venue"] == "Location on Luma"


def test_states_without_a_city_fall_back_to_the_nearest_busy_one():
    data = {
        "cities": [{**SEATTLE, "events": [{"title": "AI Week", "start": "2026-11-01T00:00:00+00:00"}]},
                   {"id": "x", "city": "Portland", "region": "OR", "lat": 45.52, "lon": -122.68, "events": []}],
        "states": {"OR": {"name": "Oregon", "cities": ["Portland"], "nearest": None}},
        "india": [],
    }
    pick = events.picks_for_web(data)["OR"]
    assert [e["title"] for e in pick["events"]] == ["AI Week"]
    assert "Nearest: Seattle" in pick["note"]
