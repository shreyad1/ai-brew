"""AI events near the reader, from Luma's public city calendars (iCal feeds)."""

import math
import re
from datetime import datetime, timedelta, timezone

import httpx

from server import AI_PATTERN, HEADERS

LUMA_ICS = "https://api.lu.ma/ics/get?entity=discover&id={place_id}"

# Luma city calendars. IDs from https://api.lu.ma/discover/bootstrap-page, checked Oct 24, 2026.
LUMA_CITIES = [
    {"id": "discplace-OgfEAh5KgfMzise", "city": "Los Angeles", "region": "CA", "lat": 34.05, "lon": -118.24},
    {"id": "discplace-BDj7GNbGlsF7Cka", "city": "San Francisco", "region": "CA", "lat": 37.77, "lon": -122.42},
    {"id": "discplace-MNBATdzid940kqJ", "city": "San Diego", "region": "CA", "lat": 32.83, "lon": -117.12},
    {"id": "discplace-3ewzk9TI8gm2QCC", "city": "Sacramento", "region": "CA", "lat": 38.57, "lon": -121.47},
    {"id": "discplace-aQeJaEtqg3shHZ1", "city": "Houston", "region": "TX", "lat": 29.79, "lon": -95.39},
    {"id": "discplace-0tPy8KGz3xMycnt", "city": "Austin", "region": "TX", "lat": 30.27, "lon": -97.74},
    {"id": "discplace-Ez9iuaZfs6AZDls", "city": "Dallas", "region": "TX", "lat": 32.79, "lon": -96.77},
    {"id": "discplace-Izx1rQVSh8njYpP", "city": "New York", "region": "NY", "lat": 40.73, "lon": -73.94},
    {"id": "discplace-VWeZ1zUvnawYHMj", "city": "Boston", "region": "MA", "lat": 42.32, "lon": -71.09},
    {"id": "discplace-FQ4E58PeBMHGTKK", "city": "Seattle", "region": "WA", "lat": 47.61, "lon": -122.33},
    {"id": "discplace-HthnjGVBzGh90sQ", "city": "Portland", "region": "OR", "lat": 45.52, "lon": -122.68},
    {"id": "discplace-NdGm35qFD0vaXNF", "city": "Chicago", "region": "IL", "lat": 41.84, "lon": -87.69},
    {"id": "discplace-C6hWuH5suHJIUqC", "city": "Atlanta", "region": "GA", "lat": 33.76, "lon": -84.42},
    {"id": "discplace-fSrrRYurTwydAGK", "city": "Miami", "region": "FL", "lat": 25.78, "lon": -80.21},
    {"id": "discplace-I94ZmQKKyVnCQKv", "city": "Denver", "region": "CO", "lat": 39.76, "lon": -104.88},
    {"id": "discplace-AANPgOymN6bqFn8", "city": "Washington, DC", "region": "DC", "lat": 38.90, "lon": -77.02},
    {"id": "discplace-VGLZZfVwOKRD1Yd", "city": "Philadelphia", "region": "PA", "lat": 40.01, "lon": -75.13},
    {"id": "discplace-Dt211oc2OdbLhnS", "city": "Pittsburgh", "region": "PA", "lat": 40.44, "lon": -79.98},
    {"id": "discplace-Vk9M1gTb4AMVXuD", "city": "Phoenix", "region": "AZ", "lat": 33.57, "lon": -112.09},
    {"id": "discplace-RF9Yq9JDUxmcpTr", "city": "Las Vegas", "region": "NV", "lat": 36.23, "lon": -115.27},
    {"id": "discplace-gxZJbB572Ls8RRu", "city": "Salt Lake City", "region": "UT", "lat": 40.78, "lon": -111.93},
    {"id": "discplace-IHi0OqR5c6t4Hb3", "city": "Minneapolis", "region": "MN", "lat": 44.96, "lon": -93.27},
    {"id": "discplace-gpqryTpxaqtM41R", "city": "Raleigh", "region": "NC", "lat": 35.83, "lon": -78.64},
    {"id": "discplace-WdZuTYoQlHeu403", "city": "Cincinnati", "region": "OH", "lat": 39.14, "lon": -84.51},
    {"id": "discplace-nkE8zpyEW5OBLlE", "city": "Detroit", "region": "MI", "lat": 42.38, "lon": -83.10},
    {"id": "discplace-CzipmKodUYN2Dfx", "city": "New Delhi", "region": "India", "lat": 28.61, "lon": 77.21},
    {"id": "discplace-Q5hkYsjZs1ZDJcU", "city": "Mumbai", "region": "India", "lat": 19.08, "lon": 72.88},
    {"id": "discplace-G0tGUVYwl7T17Sb", "city": "Bengaluru", "region": "India", "lat": 12.97, "lon": 77.59},
]

# Approximate geographic centre of each US state, used to find the nearest Luma city
# for states that don't have one.
US_STATES = {
    "AL": ("Alabama", 32.8, -86.8), "AK": ("Alaska", 61.4, -152.3), "AZ": ("Arizona", 34.2, -111.7),
    "AR": ("Arkansas", 34.9, -92.4), "CA": ("California", 37.2, -119.4), "CO": ("Colorado", 39.0, -105.5),
    "CT": ("Connecticut", 41.6, -72.7), "DE": ("Delaware", 39.0, -75.5), "DC": ("Washington, DC", 38.9, -77.0),
    "FL": ("Florida", 28.6, -82.4), "GA": ("Georgia", 32.7, -83.4), "HI": ("Hawaii", 20.8, -156.3),
    "ID": ("Idaho", 44.4, -114.6), "IL": ("Illinois", 40.0, -89.2), "IN": ("Indiana", 39.9, -86.3),
    "IA": ("Iowa", 42.1, -93.5), "KS": ("Kansas", 38.5, -98.4), "KY": ("Kentucky", 37.5, -85.3),
    "LA": ("Louisiana", 31.1, -92.0), "ME": ("Maine", 45.4, -69.2), "MD": ("Maryland", 39.0, -76.8),
    "MA": ("Massachusetts", 42.3, -71.8), "MI": ("Michigan", 44.3, -85.4), "MN": ("Minnesota", 46.3, -94.3),
    "MS": ("Mississippi", 32.7, -89.7), "MO": ("Missouri", 38.4, -92.5), "MT": ("Montana", 47.0, -109.6),
    "NE": ("Nebraska", 41.5, -99.8), "NV": ("Nevada", 39.3, -116.6), "NH": ("New Hampshire", 43.7, -71.6),
    "NJ": ("New Jersey", 40.2, -74.7), "NM": ("New Mexico", 34.4, -106.1), "NY": ("New York", 42.9, -75.5),
    "NC": ("North Carolina", 35.6, -79.4), "ND": ("North Dakota", 47.5, -100.5), "OH": ("Ohio", 40.3, -82.8),
    "OK": ("Oklahoma", 35.6, -97.5), "OR": ("Oregon", 43.9, -120.6), "PA": ("Pennsylvania", 40.9, -77.8),
    "RI": ("Rhode Island", 41.7, -71.5), "SC": ("South Carolina", 33.9, -80.9), "SD": ("South Dakota", 44.4, -100.2),
    "TN": ("Tennessee", 35.9, -86.4), "TX": ("Texas", 31.5, -99.3), "UT": ("Utah", 39.3, -111.7),
    "VT": ("Vermont", 44.1, -72.7), "VA": ("Virginia", 37.5, -78.9), "WA": ("Washington", 47.4, -120.5),
    "WV": ("West Virginia", 38.6, -80.6), "WI": ("Wisconsin", 44.6, -89.9), "WY": ("Wyoming", 43.0, -107.6),
}

LINK_PATTERN = re.compile(r"https://(?:luma\.com|lu\.ma)/\S+")


def miles_between(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Great-circle distance in miles (haversine)."""
    r = 3959
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.asin(math.sqrt(a)))


def parse_ics(text: str) -> list[dict]:
    """Minimal iCal reader: unfold continuation lines, then collect each VEVENT's fields."""
    text = re.sub(r"\r?\n[ \t]", "", text)
    events, current = [], None
    for line in text.splitlines():
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.split(";")[0]] = value.replace("\\n", "\n").replace("\\,", ",")
    return events


def fetch_city_events(city: dict, days_ahead: int = 30) -> list[dict]:
    """Upcoming AI events in one Luma city calendar."""
    response = httpx.get(LUMA_ICS.format(place_id=city["id"]), timeout=10, headers=HEADERS)
    response.raise_for_status()
    now = datetime.now(timezone.utc)
    events = []
    for raw in parse_ics(response.text):
        title = raw.get("SUMMARY", "")
        description = raw.get("DESCRIPTION", "")
        # A single passing mention of AI in a long description isn't enough to call it an AI event.
        if not AI_PATTERN.search(title) and len(AI_PATTERN.findall(description)) < 3:
            continue
        start = datetime.strptime(raw["DTSTART"], "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if not now - timedelta(hours=6) <= start <= now + timedelta(days=days_ahead):
            continue
        link = LINK_PATTERN.search(description)
        location = raw.get("LOCATION", "")
        events.append({
            "title": title,
            "start": start.isoformat(),
            # Luma often hides the address until you register, leaving only a link here.
            "venue": "Location on Luma" if location.startswith("http") else location.split(",")[0],
            "address": "" if location.startswith("http") else location,
            "link": link.group(0) if link else "https://luma.com/" + city["city"].lower().replace(" ", "-"),
            "city": city["city"],
        })
    return sorted(events, key=lambda e: e["start"])


def collect_all(days_ahead: int = 30) -> dict:
    """Events for every supported city, plus which city serves each US state."""
    cities, failed = [], []
    for city in LUMA_CITIES:
        try:
            events = fetch_city_events(city, days_ahead)
        except Exception as error:
            failed.append(f"{city['city']}: {error}")
            events = []
        cities.append({**city, "events": events})

    us_cities = [c for c in LUMA_CITIES if c["region"] != "India"]
    states = {}
    for code, (name, lat, lon) in US_STATES.items():
        in_state = [c["city"] for c in us_cities if c["region"] == code]
        if in_state:
            states[code] = {"name": name, "cities": in_state, "nearest": None}
        else:
            nearest = min(us_cities, key=lambda c: miles_between(lat, lon, c["lat"], c["lon"]))
            miles = miles_between(lat, lon, nearest["lat"], nearest["lon"])
            states[code] = {"name": name, "cities": [nearest["city"]], "nearest": f"{nearest['city']}, about {miles} miles away"}
    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "cities": cities,
        "states": states,
        "india": [c["city"] for c in LUMA_CITIES if c["region"] == "India"],
        "failed": failed,
    }


def picks_for_web(data: dict, per_place: int = 6) -> dict:
    """What the web page shows for each choice (a US state or an Indian city).

    If a place has no AI events this month, fall back to the nearest city that does, and say so.
    """
    by_city = {c["city"]: c for c in data["cities"]}
    with_events = [c for c in data["cities"] if c["events"]]

    def nearest_busy(lat: float, lon: float, region_is_india: bool) -> dict | None:
        pool = [c for c in with_events if (c["region"] == "India") == region_is_india]
        return min(pool, key=lambda c: miles_between(lat, lon, c["lat"], c["lon"]), default=None)

    def pick(label: str, city_names: list[str], lat: float, lon: float, india: bool, note: str | None) -> dict:
        events = sorted((e for name in city_names for e in by_city[name]["events"]), key=lambda e: e["start"])
        if not events:
            busy = nearest_busy(lat, lon, india)
            if busy:
                miles = miles_between(lat, lon, busy["lat"], busy["lon"])
                note = f"No AI events listed in {label} this month. Nearest: {busy['city']}, about {miles} miles away."
                events = busy["events"]
        return {"label": label, "note": note, "events": events[:per_place]}

    picks = {}
    for code, state in data["states"].items():
        _, lat, lon = US_STATES[code]
        picks[code] = pick(state["name"], state["cities"], lat, lon, False, state["nearest"] and f"Closest Luma city: {state['nearest']}.")
    for name in data["india"]:
        c = by_city[name]
        picks[name] = pick(name, [name], c["lat"], c["lon"], True, None)
    return picks


if __name__ == "__main__":
    data = collect_all()
    for city in data["cities"]:
        print(f"{city['city']:16} {len(city['events'])} AI events")
    print("failed:", data["failed"])
