"""Build the web edition: one page per issue plus an archive, ready for GitHub Pages."""

import json
import shutil
from pathlib import Path

import events
from render import env, prepare

ROOT = Path(__file__).parent
ISSUES_DIR = ROOT / "issues"
SITE_DIR = ROOT / "site"
SITE_URL = "https://shreyad1.github.io/ai-brew/"


def load_issues() -> list[dict]:
    """Every published issue, newest first. Skips the hand-written sample and the source logs."""
    paths = [p for p in ISSUES_DIR.glob("2*.json") if not p.name.endswith(".sources.json")]
    issues = [json.loads(p.read_text()) for p in paths]
    return sorted(issues, key=lambda issue: issue["date_iso"], reverse=True)


# Choices for the "Near you" picker: every US state, then the Indian cities Luma covers.
PLACES = {
    "us": sorted(((code, name) for code, (name, _, _) in events.US_STATES.items()), key=lambda p: p[1]),
    "india": [c["city"] for c in events.LUMA_CITIES if c["region"] == "India"],
}

WORDS_PER_MINUTE = 230  # average adult reading speed


def words_in(value: object) -> int:
    """Count words in every string inside a section, however deeply nested."""
    if isinstance(value, str):
        return len(value.split())
    if isinstance(value, dict):
        return sum(words_in(v) for k, v in value.items() if k not in ("link", "id", "source"))
    if isinstance(value, list):
        return sum(words_in(v) for v in value)
    return 0


def as_clock(words: int) -> str:
    seconds = max(10, round(words / WORDS_PER_MINUTE * 60 / 5) * 5)
    return f"{seconds // 60}:{seconds % 60:02d}"


def brew_times(issue: dict) -> dict[str, str]:
    """Real reading time per section, shown like a pour timer."""
    counts = {key: words_in(issue.get(key)) for key in
              ("big_pour", "builder", "office_blend", "still_roasting", "quick_sips", "long_read", "poll")}
    counts["learn"] = words_in(issue.get("word")) + words_in(issue.get("keep_brewing"))
    times = {key: as_clock(n) for key, n in counts.items()}
    times["total"] = as_clock(sum(counts.values()))
    return times


def build() -> Path:
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    (SITE_DIR / "issues").mkdir(parents=True)
    for asset in (ROOT / "site_static").iterdir():
        shutil.copy(asset, SITE_DIR / asset.name)

    try:
        data = events.collect_all()
        payload = {"generated": data["generated"], "picks": events.picks_for_web(data)}
        print(f"Events: {sum(len(c['events']) for c in data['cities'])} across {len(data['cities'])} cities")
    except Exception as error:  # events are a bonus; never block the site on them
        print(f"Events skipped: {error}")
        payload = {"generated": None, "picks": {}}
    (SITE_DIR / "events.json").write_text(json.dumps(payload))
    # Embedded in each page too, so Near You works even when a page is opened straight from disk.
    events_json = json.dumps(payload).replace("</", "<\\/")

    issues = load_issues()
    page = env.get_template("web.html.j2")
    for issue in issues:
        html = page.render(issue=prepare(issue), times=brew_times(issue), root="../", places=PLACES, events_json=events_json)
        (SITE_DIR / "issues" / f"{issue['date_iso']}.html").write_text(html)

    archive = env.get_template("archive.html.j2").render(issues=issues)
    (SITE_DIR / "index.html").write_text(archive)
    (SITE_DIR / ".nojekyll").touch()  # tells GitHub Pages to serve files as-is
    print(f"Built {len(issues)} issue page(s) into {SITE_DIR}")
    return SITE_DIR


if __name__ == "__main__":
    build()
