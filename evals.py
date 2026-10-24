"""Faithfulness evals: an LLM judge checks every sentence the agent wrote against its source.

checks.py catches invented numbers, names, and quotes. This catches the rest: claims that
use only real words but say something the source doesn't (e.g. "political ads" when the
source only says "ads").

    uv run evals.py              # judge the newest issue, update evals/summary.json
    uv run evals.py 2026-10-24   # judge one issue
    uv run evals.py --calibrate  # measure the judge itself on hand-labelled cases
"""

import json
import re
import sys
from pathlib import Path

import yaml

from llm import ask_json

ROOT = Path(__file__).parent
ISSUES_DIR = ROOT / "issues"
EVALS_DIR = ROOT / "evals"
SUMMARY = EVALS_DIR / "summary.json"

# Ideally a stronger model than the writer, but Pro models have no free-tier quota (429).
# So the judge is a Flash model run at temperature 0 with a strict rubric, and its accuracy
# is measured separately with --calibrate instead of assumed.
JUDGE_MODELS = ["gemini-flash-latest", "gemini-3.5-flash", "gemini-3.8-flash"]

JUDGE_SYSTEM = """You are a strict fact-checker for a news digest. For each numbered claim you get
the claim and the SOURCE text it was written from. Judge ONLY against that source text, never
against your own knowledge.

- "supported": everything the claim states is stated or directly implied by the source.
- "partial": the core is supported, but it adds a detail, scope, or certainty the source lacks.
- "unsupported": it states something the source does not say, or contradicts it.

Opinions and framing like "why you should care" are allowed if they add no new facts.
Return JSON: {"verdicts": [{"n": <claim number>, "verdict": "...", "reason": "<one short sentence>"}]}"""

# Fields the agent writes, and therefore the ones we judge.
WRITTEN_FIELDS = ("headline", "summary", "why", "explanation")


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"“])", text.strip())
    return [p for p in parts if len(p.split()) >= 3]


def collect_claims(issue: dict, sources: dict[str, dict]) -> list[dict]:
    """Every sentence the agent wrote, paired with the source text of its story."""
    entries = []
    for key in ("glance", "big_pour", "office_blend", "still_roasting", "quick_sips"):
        entries += [(key, e) for e in issue.get(key) or []]
    builder = issue.get("builder") or {}
    entries += [("builder", e) for e in builder.get("stories") or []]
    if builder.get("concept"):
        entries.append(("concept", builder["concept"]))
    if issue.get("long_read"):
        entries.append(("long_read", issue["long_read"]))

    claims = []
    for section, entry in entries:
        story = sources.get(entry.get("id", ""))
        if not story:
            continue
        source = f'{story["title"]}. {story["summary"]}'
        texts = [entry.get(f) for f in WRITTEN_FIELDS] + list((entry.get("explain") or {}).values())
        for text in filter(None, texts):
            for sentence in split_sentences(text):
                claims.append({"section": section, "id": entry["id"], "claim": sentence, "source": source})
    return claims


def judge(claims: list[dict], batch: int = 12) -> list[dict]:
    """Ask the judge about each claim, in batches. Returns claims with verdict and reason added."""
    judged = []
    for start in range(0, len(claims), batch):
        chunk = claims[start:start + batch]
        prompt = "\n\n".join(f"Claim {i}: {c['claim']}\nSOURCE: {c['source']}" for i, c in enumerate(chunk, 1))
        verdicts = {v["n"]: v for v in ask_json(JUDGE_SYSTEM, prompt, models=JUDGE_MODELS, temperature=0).get("verdicts", [])}
        for i, claim in enumerate(chunk, 1):
            v = verdicts.get(i, {"verdict": "unjudged", "reason": "The judge returned no verdict."})
            judged.append(claim | {"verdict": v["verdict"], "reason": v.get("reason", "")})
    return judged


def score(judged: list[dict]) -> dict:
    counted = [j for j in judged if j["verdict"] != "unjudged"]
    count = lambda verdict: sum(j["verdict"] == verdict for j in counted)
    return {
        "claims": len(counted),
        "supported": count("supported"),
        "partial": count("partial"),
        "unsupported": count("unsupported"),
        # Partial counts as half: the core fact is right, a detail isn't.
        "faithfulness": round((count("supported") + 0.5 * count("partial")) / len(counted), 3) if counted else None,
    }


def eval_issue(date: str) -> dict:
    issue = json.loads((ISSUES_DIR / f"{date}.json").read_text())
    sources = json.loads((ISSUES_DIR / f"{date}.sources.json").read_text())["sources"]
    judged = judge(collect_claims(issue, sources))
    result = {"date": date} | score(judged) | {"flagged": [j for j in judged if j["verdict"] in ("partial", "unsupported")]}

    EVALS_DIR.mkdir(exist_ok=True)
    (EVALS_DIR / f"{date}.json").write_text(json.dumps(result | {"all": judged}, indent=2))
    history = [h for h in (json.loads(SUMMARY.read_text()) if SUMMARY.exists() else []) if h["date"] != date]
    history.append({k: result[k] for k in ("date", "claims", "supported", "partial", "unsupported", "faithfulness")})
    SUMMARY.write_text(json.dumps(sorted(history, key=lambda h: h["date"]), indent=2))
    return result


def calibrate() -> dict:
    """How often does the judge agree with a human? Uses evals/judge_cases.yaml."""
    cases = yaml.safe_load((EVALS_DIR / "judge_cases.yaml").read_text())["cases"]
    judged = judge([{"claim": c["claim"], "source": c["source"]} for c in cases])
    rows = [{"claim": c["claim"], "expected": c["label"], "got": j["verdict"]} for c, j in zip(cases, judged)]
    bad = lambda label: label in ("partial", "unsupported")
    caught = sum(bad(r["got"]) for r in rows if bad(r["expected"]))
    false_alarms = sum(bad(r["got"]) for r in rows if not bad(r["expected"]))
    return {
        "cases": len(rows),
        "exact_agreement": round(sum(r["expected"] == r["got"] for r in rows) / len(rows), 3),
        "errors_caught": f"{caught} of {sum(bad(r['expected']) for r in rows)}",
        "false_alarms": f"{false_alarms} of {sum(not bad(r['expected']) for r in rows)}",
        "disagreements": [r for r in rows if r["expected"] != r["got"]],
    }


if __name__ == "__main__":
    if "--calibrate" in sys.argv:
        result = calibrate()
        EVALS_DIR.mkdir(exist_ok=True)
        (EVALS_DIR / "calibration.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
    else:
        dates = [a for a in sys.argv[1:] if not a.startswith("-")]
        if not dates:
            issues = sorted(p.stem for p in ISSUES_DIR.glob("2*.json") if not p.name.endswith(".sources.json"))
            dates = issues[-1:]
        for date in dates:
            r = eval_issue(date)
            print(f"{date}: faithfulness {r['faithfulness']} over {r['claims']} claims "
                  f"({r['supported']} supported, {r['partial']} partial, {r['unsupported']} unsupported)")
            for f in r["flagged"]:
                print(f"  [{f['verdict']}] {f['claim']}\n      -> {f['reason']}")
