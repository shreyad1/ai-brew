"""Guardrails: every number, name, and quote the LLM writes must come from the source item."""

import re

NUMBER_PATTERN = re.compile(r"\d+(?:[.,]\d+)*")
QUOTE_PATTERN = re.compile(r"[\"“]([^\"”]{4,})[\"”]")
NAME_PATTERN = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:[-'’][A-Za-z0-9]+)*")
# Capitalized words that aren't names. Without "AI" here, the LLM rewrites it as the clunky "artificial intelligence".
COMMON_TERMS = {"AI", "API", "APIs", "LLM", "LLMs", "I"}
SENTENCE_START = re.compile(r"(?:^|[.!?:]\s+|[\"“(]\s*)$")


def normalize(text: str) -> str:
    """Lowercase and unify curly quotes so matching is fair."""
    return text.lower().replace("’", "'").replace("“", '"').replace("”", '"')


def check_numbers(text: str, source: str) -> list[str]:
    """Every number in the text must appear in the source text."""
    source_numbers = {n.replace(",", "") for n in NUMBER_PATTERN.findall(source)}
    return [
        f"number '{n}' is not in the source"
        for n in NUMBER_PATTERN.findall(text)
        if n.replace(",", "") not in source_numbers
    ]


def check_quotes(text: str, source: str) -> list[str]:
    """Anything in quotation marks must be copied exactly from the source."""
    return [
        f"quote \"{q}\" is not copied exactly from the source"
        for q in QUOTE_PATTERN.findall(text)
        if normalize(q) not in normalize(source)
    ]


def check_names(text: str, source: str) -> list[str]:
    """Capitalized words (company, product, people names) must appear in the source.

    Capitalized words that start a sentence are skipped: they're usually ordinary
    words like "The". The trade-off: an invented name at a sentence start slips through.
    """
    problems = []
    for match in NAME_PATTERN.finditer(text):
        name = match.group(0)
        if SENTENCE_START.search(text[: match.start()]) or name in COMMON_TERMS:
            continue
        if normalize(name) not in normalize(source):
            problems.append(f"name '{name}' is not in the source")
    return problems


def check_text(text: str, source: str) -> list[str]:
    """All guardrail problems for one piece of LLM-written text. Empty list means it passed."""
    return check_numbers(text, source) + check_quotes(text, source) + check_names(text, source)
