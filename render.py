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


def build_menu(issue: dict) -> list[tuple[str, str]]:
    """Table of contents: one line per section that has content today."""
    menu = []
    if issue.get("big_pour"):
        menu.append(("The Big Pour", issue["big_pour"][0].get("teaser", "")))
    if issue.get("office_blend"):
        menu.append(("Office Blend", issue["office_blend"][0].get("teaser", "")))
    if issue.get("still_roasting"):
        menu.append(("Still Roasting", "launching soon"))
    if issue.get("quick_sips"):
        menu.append(("Quick Sips", f"{len(issue['quick_sips'])} one-liners"))
    if issue.get("builder"):
        menu.append(("The Builder's Bar", "for engineers"))
    if issue.get("long_read"):
        menu.append(("The Long Read", f"from {issue['long_read']['source']}"))
    if issue.get("word"):
        menu.append(("Word of the Day", issue["word"]["term"]))
    return menu


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
