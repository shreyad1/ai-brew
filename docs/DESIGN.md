# The AI Brew: design notes

A daily AI news briefing written by an LLM agent. This document covers how it works, the decisions behind it, how it fails, and what would change at larger scale.

## Goal and the one hard constraint

**Goal:** a 3-minute, plain-English AI briefing every day, readable by non-engineers, with a section for engineers.

**Constraint:** zero invented content. Every fact, number, name, quote, date, and link must trace back to a real source item. A summarizer that is fluent but occasionally wrong is worse than no summarizer, because readers can't tell which sentences to trust.

Everything below follows from that constraint.

## Architecture

```
sources.yaml ─► feeds.py ──► filters.py ──► server.py (6 MCP tools)
 (19 RSS)       fetch,        clean, AI /         │
                timeout,      sponsored /         ▼
                per-feed      upcoming,      digest.py ── llm.py (Gemini, fallback models)
                failures      dedupe              │  ids + titles + summaries only
                                                  ▼
                                             checks.py   numbers, names, quotes vs source
                                                  │  fail → one rewrite → still fail → drop
                                                  ▼
                                    issue JSON + sources.json log
                                                  │
                         ┌────────────────────────┼─────────────────────────┐
                         ▼                        ▼                         ▼
                    evals.py              build_site.py               render.py
                LLM judge, scored      web app (Cloudflare Pages)   email (Buttondown)

Luma city iCal feeds ─► events.py ─► "Near you" in the app and the get_ai_events tool
GitHub Actions: daily.yml (write + judge + commit) → pages.yml (build + deploy); tests.yml on every push
```

The MCP server and the agent use the same tool functions, so Claude Desktop sees exactly the data the newsletter is written from.

## Key decisions

### 1. The model never sees or writes links
The LLM receives `id: title | summary` lines and returns JSON that refers to stories by id. Code attaches every link, source name, image, and date from the original feed item (`digest.attach_sources`).
**Why:** link hallucination is the most damaging failure for a news product and the easiest to remove structurally. It removes a whole class of errors instead of checking for them.

### 2. Deterministic checks before any model-based check
`checks.py` rejects any number, capitalized name, or quoted phrase that doesn't appear in that story's source text. A failing entry gets exactly one rewrite with its specific problems listed; if it still fails, it is dropped. If fewer than 3 top stories survive, the issue isn't published.
**Why:** these checks are cheap, deterministic, explainable ("number '40' is not in the source"), and testable. One retry balances quality against cost and latency; unbounded retries can loop.
**Known gaps:** a capitalized word at the start of a sentence isn't checked (it's usually "The"); claims made only of real words ("political ads" from a source about "ads") pass. That gap is what the judge covers.

### 3. An LLM judge, measured instead of trusted
`evals.py` splits everything the agent wrote into sentences and asks a judge model to label each one supported / partial / unsupported against its source. Faithfulness = (supported + 0.5 × partial) / judged.
The judge is calibrated on `evals/judge_cases.yaml`: 14 hand-labelled cases built from real sources, 8 of them with planted or partial errors. Current result: 14/14 agreement, 8/8 errors caught, 0/6 false alarms.
**Trade-off:** the free tier has no quota for Pro models, so the judge is a Flash model, the same family as the writer. Self-grading bias is the risk; calibration on human labels is the mitigation. The judge runs after writing and never blocks publishing.
**What it found on day one:** 91.7% over 30 sentences. The flags were real: a concept definition written from model knowledge rather than the source, and simplified retellings that dropped the qualifier "AI-generated". Both became prompt rules the next day.

### 4. Dedupe with word overlap, not embeddings
Headlines are compared with Jaccard similarity over non-stop-words; ≥ 0.3 means the same story. The threshold was tuned on real headlines: it merged the true duplicates (0.33, 0.36) and kept apart a different story about the same company (0.23).
**Trade-off:** it misses paraphrased duplicates (two Block voice-model headlines sharing almost no words) and can merge very short headlines (a test documents this). Embeddings would fix both, at the cost of an API call or model per run. The LLM editor is the second line of defence today.

### 5. Feed hygiene is configuration, not code
`sources.yaml` holds every feed with its section and flags: `ai_filter` for outlets that mix in non-AI news, `images: false` for feeds whose images are diagrams. Sponsored posts are detected by title, summary, **and category**, because MIT Technology Review marks paid posts only with a `sponsored` category.
**Why:** adding or fixing a source should be a one-line change that a non-engineer can review.

### 6. Human-owned content is copied, never generated
Word of the Day, learning resources, and polls come from YAML files a person reviewed. The agent picks the next unused entry. Unreviewed words produce a warning in the run log.

### 7. A static app with its data built in
The web app is one HTML page with every issue and the events embedded as JSON, served from Cloudflare Pages. Saved stories and settings live in `localStorage`.
**Why:** no server to run or secure, free hosting, instant tab switches, and it works offline or opened from disk. **Trade-off:** saves don't sync across devices, and page size grows with the archive (about 48 KB with one issue; fine for years, then paginate).

## Failure modes and what happens

| Failure | Behaviour |
| --- | --- |
| A feed times out, 4xx/5xx, or blocks the user agent | Skipped and listed in `failed_feeds`; the rest continue (10 s timeout per feed) |
| A feed goes stale or adds sponsored posts | Age filter drops old items; sponsored filter drops paid posts |
| Gemini model overloaded (503), out of quota (429), or slow (504) | `llm.py` falls through a list of models; other errors raise immediately so bugs aren't hidden |
| The model returns the wrong JSON shape | Missing fields default safely; entries with unknown ids are rejected |
| The model invents a number, name, or quote | One rewrite, then the entry is dropped and logged |
| Too few stories survive | Issue isn't published; the workflow fails and GitHub emails the owner |
| The judge is unavailable | Eval step is skipped (`continue-on-error`); the issue still publishes |
| Luma is down | The app builds without events and says so; nothing else is blocked |
| A re-run on the same day | Overwrites that day's issue and keeps its number |

Every issue saves `issues/<date>.sources.json` with all source items, the model's raw draft, what the checks flagged, and what was dropped, so any sentence can be traced back.

## Testing

50 pytest tests, all HTTP mocked, run on every push (`tests.yml`). They cover the guardrails, filters, dedupe (including its documented weakness), image extraction, feed failures, tool input clamping, iCal parsing, the agent's rewrite-then-drop behaviour, link attachment, HTML escaping in the email, and the eval scoring and calibration maths.

## At 100× scale

| Today | At 100× (many newsletters, many readers) |
| --- | --- |
| 19 feeds fetched sequentially once a day | Async fetching with a cache (conditional GETs, ETags), a queue per source |
| Jaccard dedupe | Embedding similarity with a vector index, plus story threading across days |
| One LLM call for the issue | Per-section calls in parallel, with cost and latency tracked per run |
| Judge on every sentence | Judge on a sample plus every sentence the checks touched; human review queue for low scores |
| JSON files in git | A small database for issues, sources, and eval results; git only for config |
| One static page with all issues embedded | Paginated archive and search served from an index |
| Free-tier models with fallbacks | Paid tier with a stronger judge than writer, and an eval gate that blocks publishing below a threshold |

## What I'd do next

1. Embedding-based dedupe and an "ask the archive" search (retrieval-augmented, with citations).
2. Make the eval a publishing gate: hold any issue below 90% for human review.
3. Per-subscriber email sections (city for events, engineer mode) once email sending is live.
