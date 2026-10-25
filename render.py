"""Turn an issue's content (a dict) into the HTML email."""

import json
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

TEMPLATES_DIR = Path(__file__).parent / "templates"

# StrictUndefined makes a typo like {{ story.titel }} fail loudly instead of rendering blank.
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html", "j2"]),
    undefined=StrictUndefined,
)


def first(items: list | None, key: str) -> str:
    return (items or [{}])[0].get(key, "")


def build_menu(issue: dict) -> list[tuple[str, str]]:
    """"In today's issue": each section that has content, with its first real headline."""
    builder = issue.get("builder") or {}
    rows = [
        ("Top Stories", first(issue.get("big_pour"), "headline")),
        ("AI at Work", first(issue.get("office_blend"), "headline")),
        ("Coming Up", f"{len(issue['still_roasting'])} things to watch" if issue.get("still_roasting") else ""),
        ("In Brief", f"{len(issue['quick_sips'])} quick headlines" if issue.get("quick_sips") else ""),
        ("For Engineers", first(builder.get("stories"), "headline") or (builder.get("concept") or {}).get("term", "")),
        ("The Long Read", (issue.get("long_read") or {}).get("headline", "")),
        ("Word of the Day", (issue.get("word") or {}).get("term", "")),
    ]
    return [(name, line) for name, line in rows if line]


def prepare(issue: dict) -> dict:
    """Fill in missing sections and the menu, so the strict templates never hit a missing key."""
    sections = ["glance", "big_pour", "office_blend", "still_roasting", "quick_sips",
                "builder", "long_read", "word", "keep_brewing", "poll"]
    issue = {key: None for key in sections} | {"web_url": None} | issue
    issue["menu"] = build_menu(issue)
    return issue


def render_email(issue: dict) -> str:
    """Fill the email template with one issue's content."""
    return env.get_template("email.html.j2").render(issue=prepare(issue))


if __name__ == "__main__":
    source = Path(sys.argv[1])
    issue = json.loads(source.read_text())
    output = source.with_suffix(".html")
    output.write_text(render_email(issue))
    print(f"Wrote {output}")
