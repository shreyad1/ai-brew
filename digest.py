"""The digest agent: gather stories, let the LLM pick and write, check every line, render the issue."""

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from checks import check_text
from llm import ask_json
from render import render_email
from server import get_ai_news, get_company_ai_updates, get_dev_updates, get_long_reads, get_upcoming

ROOT = Path(__file__).parent
ISSUES_DIR = ROOT / "issues"
TIMEZONE = ZoneInfo("America/Chicago")
MIN_TOP_STORIES = 3  # fail safe: fewer good stories than this and we don't publish

SYSTEM_PROMPT = """You are the editor of The Daily AI Cup, a short, warm morning newsletter about AI
for busy people, many of them not technical. You get a list of real news items, each with an id.

Rules you must follow:
- Use ONLY the facts in each item's title and summary. Never add facts, numbers, dates, names, or quotes.
- Only put words in quotation marks if they are copied exactly from the item.
- Plain English. Explain jargon in simple words. No hype words (revolutionary, game-changing, etc.).
- Never write links or source names. Refer to items only by their id.
- Each id may be used once in the whole issue (except in "glance", which summarizes the top stories).
- If an item's text is too thin to summarize, skip it.
- Keep every qualifier and scope from the source: "AI-generated ads" must not become "ads",
  "for Pro and Max users" must not become "for everyone". Simplify words, never the meaning.
- Name things the way the source does. Don't rename them (e.g. "AI models" must not become "political models").

Return JSON with exactly this shape:
{
  "glance": [              // 4 bullets: the day's most important AI industry news for someone with 30 seconds.
    {"id": "...", "summary": "one plain sentence, max 18 words, starting with the company or subject"}
  ],                       // Use n or w ids. These may repeat ids used in other sections.
  "big_pour": [            // 3 items from ids starting with "n". The first is the lead story.
    {"id": "...", "headline": "max 9 words, plain, may be playful",
     "teaser": "max 6 words for the table of contents",
     "summary": "1-2 sentences, max 35 words",
     "why": "lead story only: max 18 words on why a normal reader should care, no new facts",
     "explain": "lead story only: {\"kid\": ..., \"pm\": ..., \"engineer\": ...}, the same facts retold
                 for a 10-year-old, a product manager, and a software engineer. Max 40 words each.
                 Same facts only: change the words and the angle, never add information, and keep every
                 qualifier (e.g. "AI-generated", "for paid users")."}
  ],
  "office_blend": [        // 2 items from ids starting with "w": real companies using AI. Prefer customer stories over product tutorials.
    {"id": "...", "headline": "max 9 words", "teaser": "max 6 words", "summary": "1-2 sentences, max 35 words"}
  ],
  "still_roasting": [      // up to 3 items from ids starting with "u": things not released yet.
    {"id": "...", "summary": "one sentence, max 25 words"}
  ],
  "quick_sips": [          // 3 more items from "n" or "w" ids not used above.
    {"id": "...", "summary": "one sentence, max 22 words, starting with the company or product name"}
  ],
  "builder": {             // for software engineers, from ids starting with "d".
    "stories": [{"id": "...", "label": "2-3 words like New tool, Benchmark, Open standard",
                 "headline": "max 9 words", "summary": "1-2 sentences, max 35 words"}],   // 2 items
    "concept": {"id": "the d-item that mentions it", "term": "a technical term appearing in this week's d-items",
                "explanation": "max 40 words, using ONLY what the d-item's text says about the term and where it
                                showed up in the news. If the text doesn't explain the term, don't define it from
                                your own knowledge: pick a different term, or omit concept entirely"}
  },
  "long_read": {"id": "one id starting with l",
                "headline": "the essay's title, lightly shortened if needed",
                "summary": "1-2 sentences, max 35 words, attributing opinions to the newsletter"}
}"""


def gather() -> tuple[dict[str, dict], list[str]]:
    """Call every tool and give each story a short id the LLM can refer to."""
    news = get_ai_news(days=1, limit=25)
    if len(news["stories"]) < 6:  # slow news day (or weekend): look a bit further back
        news = get_ai_news(days=2, limit=25)
    batches = {
        "n": news,
        "w": get_company_ai_updates(days=7, limit=15),
        "u": get_upcoming(days=7, limit=8),
        "d": get_dev_updates(days=4, limit=12),
        "l": get_long_reads(days=14, limit=8),
    }
    pool: dict[str, dict] = {}
    failed: list[str] = []
    for prefix, result in batches.items():
        items = result.get("stories") or result.get("items") or []
        for i, story in enumerate(items, start=1):
            pool[f"{prefix}{i}"] = story
        failed += result["failed_feeds"]
    return pool, failed


def prompt_for(pool: dict[str, dict]) -> str:
    """The LLM sees only ids, titles, and summaries. Links and sources stay with the code."""
    lines = [f'{item_id}: {s["title"]} | {s["summary"]}' for item_id, s in pool.items()]
    return "Today's items:\n" + "\n".join(lines)


def source_text(story: dict) -> str:
    return f'{story["title"]} {story["summary"]}'


def entry_problems(entry: dict, pool: dict[str, dict]) -> list[str]:
    """Check every LLM-written field of one entry against its own source item."""
    story = pool.get(entry.get("id", ""))
    if story is None:
        return [f"unknown id {entry.get('id')!r}"]
    fields = ("headline", "teaser", "summary", "why", "explanation", "label")
    return [p for f in fields if entry.get(f) for p in check_text(entry[f], source_text(story))]


def all_entries(draft: dict) -> list[dict]:
    """Every story entry in the draft, wherever it sits."""
    entries = []
    for key in ("glance", "big_pour", "office_blend", "still_roasting", "quick_sips"):
        entries += draft.get(key) or []
    builder = draft.get("builder") or {}
    entries += builder.get("stories") or []
    entries += [e for e in (builder.get("concept"), draft.get("long_read")) if e]
    return entries


def fix_or_drop(draft: dict, pool: dict[str, dict], log: dict) -> dict:
    """Ask the LLM to rewrite failing entries once. Anything still failing is dropped."""
    failing = {e["id"]: entry_problems(e, pool) for e in all_entries(draft) if entry_problems(e, pool)}
    log["first_check"] = failing
    if failing:
        request = {
            "instructions": "These entries broke the rules. Rewrite each using ONLY its source text. "
                            "Keep the same id and fields. Return {\"fixed\": [entries]}.",
            "entries": [
                {"entry": e, "problems": failing[e["id"]], "source": source_text(pool[e["id"]])}
                for e in all_entries(draft) if e.get("id") in failing and e["id"] in pool
            ],
        }
        fixed = {e["id"]: e for e in ask_json(SYSTEM_PROMPT, json.dumps(request)).get("fixed", [])}
        replace = lambda e: fixed.get(e.get("id"), e)
        for key in ("glance", "big_pour", "office_blend", "still_roasting", "quick_sips"):
            draft[key] = [replace(e) for e in draft.get(key) or []]
        if draft.get("builder"):
            draft["builder"]["stories"] = [replace(e) for e in draft["builder"].get("stories") or []]
            if draft["builder"].get("concept"):
                draft["builder"]["concept"] = replace(draft["builder"]["concept"])
        if draft.get("long_read"):
            draft["long_read"] = replace(draft["long_read"])

    dropped = []
    keep = lambda e: not entry_problems(e, pool) or dropped.append({"id": e.get("id"), "problems": entry_problems(e, pool)})
    for key in ("glance", "big_pour", "office_blend", "still_roasting", "quick_sips"):
        draft[key] = [e for e in draft.get(key) or [] if keep(e)]
    if draft.get("builder"):
        draft["builder"]["stories"] = [e for e in draft["builder"].get("stories") or [] if keep(e)]
        concept = draft["builder"].get("concept")
        if concept and not keep(concept):
            draft["builder"]["concept"] = None
    if draft.get("long_read") and not keep(draft["long_read"]):
        draft["long_read"] = None
    log["dropped"] = dropped
    return draft


EXPLAIN_AUDIENCES = {"kid": "a 10-year-old", "pm": "a product manager", "engineer": "a software engineer"}
EXPLAIN_SYSTEM = ("You retell news for different readers. Use ONLY facts in the source text. "
                  "Never add facts, numbers, names, or quotes. Keep every qualifier and scope from the source "
                  "(e.g. 'AI-generated', 'for paid users'): simplify the words, never the meaning. Reply in JSON.")


def check_explainers(draft: dict, pool: dict[str, dict], log: dict) -> None:
    """The lead story's three retellings get the same fact checks. One rewrite, then drop what fails."""
    lead = (draft.get("big_pour") or [None])[0]
    if not lead or not isinstance(lead.get("explain"), dict):
        return
    source = source_text(pool[lead["id"]])
    explain = {k: v for k, v in lead["explain"].items() if k in EXPLAIN_AUDIENCES and isinstance(v, str)}
    failing = {k: check_text(v, source) for k, v in explain.items() if check_text(v, source)}
    if failing:
        request = {
            "instructions": "Rewrite each retelling using ONLY the source text. Return {\"explain\": {audience: text}}.",
            "source": source,
            "retellings": {k: {"for": EXPLAIN_AUDIENCES[k], "text": explain[k], "problems": p} for k, p in failing.items()},
        }
        explain |= ask_json(EXPLAIN_SYSTEM, json.dumps(request)).get("explain", {})
    lead["explain"] = {k: v for k, v in explain.items() if not check_text(v, source)} or None
    log["explain_dropped"] = sorted(set(EXPLAIN_AUDIENCES) - set(lead["explain"] or {}))


def attach_sources(draft: dict, pool: dict[str, dict]) -> dict:
    """The code, not the LLM, adds every link, source name, and stated date."""
    for entry in all_entries(draft):
        story = pool[entry["id"]]
        entry["link"] = story["link"]
        entry["source"] = story["source"]
        entry["image"] = story.get("image")
        if entry["id"].startswith("u"):
            entry["date_mentioned"] = story.get("date_mentioned")
    # Optional fields the LLM may leave out; the strict template needs them present.
    for entry in draft.get("big_pour") or []:
        entry.setdefault("why", None)
        entry.setdefault("explain", None)
    if draft.get("builder"):
        draft["builder"].setdefault("stories", [])
        draft["builder"].setdefault("concept", None)
    return draft


def next_from(path: Path, list_key: str, name_key: str) -> dict | None:
    """The first item in a reviewed YAML list that hasn't been used yet."""
    data = yaml.safe_load(path.read_text())
    items = list_key(data) if callable(list_key) else data[list_key]
    used = set(data.get("used") or [])
    return next((item for item in items if item[name_key] not in used), None)


def mark_used(path: Path, name: str) -> None:
    data = yaml.safe_load(path.read_text())
    data["used"] = (data.get("used") or []) + [name]
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def pick_owned_content(log: dict) -> tuple[dict | None, dict | None, dict | None]:
    """Word of the Day, Keep Brewing, and the poll come from files a human reviewed."""
    path_words = ROOT / "learning_path.yaml"
    weeks = yaml.safe_load(path_words.read_text())["weeks"]
    word = None
    for week in weeks:
        nxt = next_from(path_words, lambda d, w=week: w["words"], "term")
        if nxt:
            word = {**nxt, "theme": week["theme"], "day": week["words"].index(nxt) + 1}
            break
    if word and not word.get("reviewed"):
        log["warnings"].append(f"Word of the Day '{word['term']}' is not marked reviewed in learning_path.yaml")

    resource = next_from(ROOT / "resources.yaml", "resources", "name")
    poll_data = yaml.safe_load((ROOT / "polls.yaml").read_text())
    used_polls = poll_data.get("used") or []
    poll = next((p for p in poll_data["polls"] if p["question"] not in used_polls), None)
    last = next((p for p in poll_data["polls"] if used_polls and p["question"] == used_polls[-1]), None)
    if poll:
        poll = {"question": poll["question"], "last_results": last["results"] if last else None}
    return word, resource, poll


def build_issue(dry_run: bool = False) -> Path | None:
    now = datetime.now(TIMEZONE)
    log: dict = {"generated_at": now.isoformat(), "warnings": []}

    pool, failed = gather()
    log["failed_feeds"] = failed
    log["sources"] = pool
    print(f"Gathered {len(pool)} items ({len(failed)} feeds failed). Asking the LLM to write...")

    draft = ask_json(SYSTEM_PROMPT, prompt_for(pool))
    log["llm_draft"] = json.loads(json.dumps(draft))
    draft = fix_or_drop(draft, pool, log)
    check_explainers(draft, pool, log)
    draft = attach_sources(draft, pool)

    word, resource, poll = pick_owned_content(log)
    # Earlier issues only: a re-run on the same day must keep the same number.
    past = [p for p in ISSUES_DIR.glob("2*.json")
            if not p.name.endswith(".sources.json") and p.stem < now.date().isoformat()]
    issue = draft | {
        "number": len(past) + 1,
        "date_iso": now.date().isoformat(),
        "date_long": now.strftime("%A · %-d %B %Y"),
        "read_minutes": 3,
        "web_url": f"https://thedailyaicup.pages.dev/#/issue/{now.date().isoformat()}",
        "reply_to": "shreyadeshpande119@gmail.com",
        "subscribe_url": "#",
        "unsubscribe_url": "#",
        "sign_off": "That's the last sip. See you next morning.",
        "word": word,
        "keep_brewing": resource,
        "poll": poll,
    }

    stem = ISSUES_DIR / now.date().isoformat()
    stem.with_suffix(".sources.json").write_text(json.dumps(log, indent=2, default=str))

    if len(issue.get("big_pour") or []) < MIN_TOP_STORIES:
        print(f"Only {len(issue.get('big_pour') or [])} top stories passed the checks. Not publishing. See {stem}.sources.json")
        return None

    stem.with_suffix(".json").write_text(json.dumps(issue, indent=2))
    stem.with_suffix(".html").write_text(render_email(issue))
    if not dry_run:
        for path, name in [(ROOT / "learning_path.yaml", word and word["term"]),
                           (ROOT / "resources.yaml", resource and resource["name"]),
                           (ROOT / "polls.yaml", poll and poll["question"])]:
            if name:
                mark_used(path, name)
    print(f"First check flagged {len(log['first_check'])} entries; dropped {len(log['dropped'])} after one rewrite.")
    for warning in log["warnings"]:
        print("Warning:", warning)
    return stem.with_suffix(".html")


if __name__ == "__main__":
    result = build_issue(dry_run="--dry-run" in sys.argv)
    if result:
        print(f"Wrote {result}")
    else:
        sys.exit(1)
