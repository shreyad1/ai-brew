"""The agent's safety steps: unknown ids, one rewrite then drop, and links attached by code."""

import json
from pathlib import Path

import digest
from render import render_email

POOL = {
    "n1": {"title": "OpenAI raises $30B", "summary": "OpenAI is raising $30B at a $1.25T valuation.",
           "link": "https://tc.com/openai", "source": "TechCrunch", "image": None},
    "n2": {"title": "Canva launches an image model", "summary": "Canva launched Canva Craft.",
           "link": "https://verge.com/canva", "source": "The Verge", "image": "https://img/c.jpg"},
}


def test_unknown_id_is_a_problem():
    assert digest.entry_problems({"id": "n99", "summary": "x"}, POOL) == ["unknown id 'n99'"]


def test_good_entry_passes():
    assert digest.entry_problems({"id": "n1", "headline": "OpenAI raises $30B", "summary": "OpenAI is raising $30B."}, POOL) == []


def test_failing_entry_is_rewritten_once_then_dropped_if_still_bad(monkeypatch):
    calls = []

    def fake_llm(system, prompt):
        calls.append(prompt)
        return {"fixed": [{"id": "n1", "headline": "OpenAI raises $40B", "summary": "Backed by Microsoft."}]}

    monkeypatch.setattr(digest, "ask_json", fake_llm)
    draft = {"big_pour": [{"id": "n1", "headline": "OpenAI raises $40B", "summary": "x"},
                          {"id": "n2", "headline": "Canva launches an image model", "summary": "Canva launched Canva Craft."}]}
    log = {}
    result = digest.fix_or_drop(draft, POOL, log)
    assert len(calls) == 1                       # exactly one rewrite request
    assert [e["id"] for e in result["big_pour"]] == ["n2"]
    assert log["dropped"][0]["id"] == "n1"


def test_fixed_entry_is_kept(monkeypatch):
    monkeypatch.setattr(digest, "ask_json", lambda s, p: {"fixed": [{"id": "n1", "headline": "OpenAI raises $30B", "summary": "OpenAI is raising $30B."}]})
    result = digest.fix_or_drop({"big_pour": [{"id": "n1", "headline": "OpenAI raises $99B", "summary": "x"}]}, POOL, {})
    assert result["big_pour"][0]["headline"] == "OpenAI raises $30B"


def test_links_sources_and_images_come_from_the_feed_not_the_llm():
    draft = {"big_pour": [{"id": "n2", "headline": "Canva ships", "summary": "Canva launched Canva Craft.", "link": "https://made-up.example"}]}
    entry = digest.attach_sources(draft, POOL)["big_pour"][0]
    assert entry["link"] == "https://verge.com/canva"
    assert entry["source"] == "The Verge"
    assert entry["image"] == "https://img/c.jpg"


def test_bad_explainer_versions_are_dropped_one_by_one(monkeypatch):
    monkeypatch.setattr(digest, "ask_json", lambda s, p: {"explain": {"pm": "OpenAI is raising $45B."}})
    lead = {"id": "n1", "explain": {"kid": "OpenAI wants $30B.", "pm": "OpenAI is raising $45B.", "engineer": "OpenAI raises $30B."}}
    log = {}
    digest.check_explainers({"big_pour": [lead]}, POOL, log)
    assert set(lead["explain"]) == {"kid", "engineer"}
    assert log["explain_dropped"] == ["pm"]


def test_email_renders_the_sample_issue_and_escapes_html():
    issue = json.loads((Path(__file__).parent.parent / "issues" / "sample.json").read_text())
    issue["big_pour"][0]["headline"] = "<script>alert(1)</script>"
    html = render_email(issue)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "Top Stories" in html


def test_glance_bullets_get_real_links_and_go_through_the_checks(monkeypatch):
    monkeypatch.setattr(digest, "ask_json", lambda s, p: {"fixed": []})
    draft = {"glance": [{"id": "n1", "summary": "OpenAI is raising $30B at a $1.25T valuation."},
                        {"id": "n2", "summary": "Canva raised $90M for its model."}]}
    draft = digest.fix_or_drop(draft, POOL, {})
    draft = digest.attach_sources(draft, POOL)
    assert [g["id"] for g in draft["glance"]] == ["n1"]          # the invented $90M bullet is dropped
    assert draft["glance"][0]["link"] == "https://tc.com/openai"  # link from the feed, not the model
