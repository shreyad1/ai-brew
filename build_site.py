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

    # The app is one page with every issue and the events built in, so it works offline too.
    issues = [prepare(issue) for issue in load_issues()]
    app_data = json.dumps({"issues": issues, "events": payload}).replace("</", "<\\/")
    (SITE_DIR / "index.html").write_text(env.get_template("app.html.j2").render(places=PLACES, data_json=app_data))

    # Old per-issue links (and email links) forward into the app.
    for issue in issues:
        target = f"../#/issue/{issue['date_iso']}"
        (SITE_DIR / "issues" / f"{issue['date_iso']}.html").write_text(
            f'<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{SITE_URL}#/issue/{issue["date_iso"]}"><a href="{target}">Open this issue</a>'
        )
    (SITE_DIR / ".nojekyll").touch()  # tells GitHub Pages to serve files as-is
    print(f"Built the app with {len(issues)} issue(s) into {SITE_DIR}")
    return SITE_DIR


if __name__ == "__main__":
    build()
