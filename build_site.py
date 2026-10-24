"""Build the web edition: one page per issue plus an archive, ready for GitHub Pages."""

import json
import shutil
from pathlib import Path

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


def build() -> Path:
    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    (SITE_DIR / "issues").mkdir(parents=True)
    for asset in (ROOT / "site_static").iterdir():
        shutil.copy(asset, SITE_DIR / asset.name)

    issues = load_issues()
    page = env.get_template("web.html.j2")
    for issue in issues:
        html = page.render(issue=prepare(issue), root="../")
        (SITE_DIR / "issues" / f"{issue['date_iso']}.html").write_text(html)

    archive = env.get_template("archive.html.j2").render(issues=issues)
    (SITE_DIR / "index.html").write_text(archive)
    (SITE_DIR / ".nojekyll").touch()  # tells GitHub Pages to serve files as-is
    print(f"Built {len(issues)} issue page(s) into {SITE_DIR}")
    return SITE_DIR


if __name__ == "__main__":
    build()
