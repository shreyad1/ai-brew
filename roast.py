"""The Roast Meter: how intense today's AI news is, from signals counted in the feeds."""

import re

LEVELS = ["Light", "Medium", "Dark", "Espresso"]
# Score cutoffs for Medium, Dark, Espresso. First guesses: tune them after a few weeks of
# real scores (each issue's score and reasons are saved in its sources.json log).
CUTOFFS = [6, 11, 16]

LAUNCH = re.compile(r"\b(launch(?:es|ed)?|releases?d?|unveils?|introduc(?:es|ed)|debuts?|rolls? out|now available|generally available|open[- ]sources?)\b", re.I)
FUNDING = re.compile(r"\b(rais(?:es|ed|ing)|funding|valuation|acquir(?:es|ed)|acquisition|IPO|Series [A-F])\b", re.I)
POLICY = re.compile(r"\b(law|bill|regulat\w*|ban(?:s|ned)?|lawsuit|sues?|court|ruling|FTC|EU AI Act|Congress|senate)\b", re.I)


def roast(news: list[dict]) -> dict:
    """Score today's news stories and name the roast level, with the reasons behind it."""
    text = lambda s: f"{s['title']} {s['summary']}"
    biggest = max(news, key=lambda s: len(s.get("covered_by", [])), default=None)
    widest = len(biggest["covered_by"]) if biggest else 0
    launches = sum(bool(LAUNCH.search(text(s))) for s in news)
    funding = sum(bool(FUNDING.search(text(s))) for s in news)
    policy = sum(bool(POLICY.search(text(s))) for s in news)

    # A story every outlet covers matters most; volume of launches, money, and policy adds up.
    score = 3 * max(widest - 1, 0) + launches + funding + policy + len(news) // 5
    level = LEVELS[sum(score >= cutoff for cutoff in CUTOFFS)]
    reasons = [f"{len(news)} AI stories", f"{launches} launches", f"{funding} money moves", f"{policy} policy stories"]
    if widest > 1:
        reasons.insert(0, f"top story covered by {widest} outlets")
    return {"level": level, "score": score, "reasons": reasons, "position": LEVELS.index(level)}
