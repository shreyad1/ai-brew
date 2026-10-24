"""Faithfulness evals: claim collection, scoring, and judge calibration (judge is faked)."""

import evals

SOURCES = {"n1": {"title": "Pennsylvania will require labels on AI ads", "summary": "The governor signed the law."}}


def test_split_sentences_drops_fragments():
    assert evals.split_sentences("The law passed. Labels are required on ads. OK.") == [
        "The law passed.", "Labels are required on ads."]


def test_collect_claims_covers_every_written_field_including_explainers():
    issue = {"big_pour": [{"id": "n1", "headline": "Pennsylvania requires AI ad labels",
                           "summary": "The governor signed a law. Ads made with AI need labels.",
                           "why": "You will know when ads use AI.",
                           "explain": {"kid": "A new rule says AI ads need a sticker."},
                           "link": "https://x", "source": "The Verge"}]}
    claims = evals.collect_claims(issue, SOURCES)
    assert len(claims) == 5
    assert all(c["source"].startswith("Pennsylvania will require") for c in claims)


def test_entries_without_a_known_source_are_skipped():
    assert evals.collect_claims({"quick_sips": [{"id": "n9", "summary": "Something happened today."}]}, SOURCES) == []


def test_score_counts_partial_as_half_and_ignores_unjudged():
    judged = [{"verdict": "supported"}] * 6 + [{"verdict": "partial"}] * 2 + [{"verdict": "unsupported"}] + [{"verdict": "unjudged"}]
    assert evals.score(judged) == {"claims": 9, "supported": 6, "partial": 2, "unsupported": 1, "faithfulness": 0.778}


def test_judge_batches_claims_and_marks_missing_verdicts(monkeypatch):
    calls = []

    def fake_judge(system, prompt, models=None, temperature=0.3):
        calls.append(prompt)
        n = prompt.count("Claim ")
        return {"verdicts": [{"n": i, "verdict": "supported", "reason": "ok"} for i in range(1, n)]}  # skips the last

    monkeypatch.setattr(evals, "ask_json", fake_judge)
    claims = [{"claim": f"Sentence number {i}.", "source": "src"} for i in range(30)]
    judged = evals.judge(claims, batch=25)  # explicit batch size
    assert len(calls) == 2
    assert [j["verdict"] for j in judged].count("unjudged") == 2


def test_calibration_reports_caught_errors_and_false_alarms(monkeypatch, tmp_path):
    (tmp_path / "judge_cases.yaml").write_text(
        "cases:\n"
        "  - {source: s, claim: a, label: supported}\n"
        "  - {source: s, claim: b, label: unsupported}\n"
        "  - {source: s, claim: c, label: partial}\n")
    monkeypatch.setattr(evals, "EVALS_DIR", tmp_path)
    monkeypatch.setattr(evals, "ask_json", lambda *a, **k: {"verdicts": [
        {"n": 1, "verdict": "unsupported"}, {"n": 2, "verdict": "unsupported"}, {"n": 3, "verdict": "supported"}]})
    result = evals.calibrate()
    assert result["errors_caught"] == "1 of 2"
    assert result["false_alarms"] == "1 of 1"
    assert result["exact_agreement"] == 0.333
