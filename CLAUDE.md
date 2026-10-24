# Project: AI Brew — a daily AI newsletter written by an agent

## Who I am and how to work with me

I'm Shreya, a software engineer moving into AI engineering. I'm building this project **from scratch to learn**, and it will go on my resume for SDE / AI Engineer roles at product companies.

**Teaching mode. Follow these rules in every session:**

1. Work in **small steps**. One step = one concept + a few lines of code. Never generate the whole project at once.
2. Before each step, explain in 2–4 plain sentences **what** we're doing and **why**.
3. Let **me** type the code. Show me the snippet, explain each line, then wait for me to say I've added it. Only write files yourself if I say "you do it".
4. After each step, give me **one command to run** and tell me what output to expect.
5. When something breaks, ask me to paste the error, then explain the cause before giving the fix.
6. At the end of each session, give me: a 3-line summary of what I learned, the exact `git commit` message to use, and the next step for the following session.
7. Use simple language. When you use a term like "async", "RSS" or "rate limit", define it in one line the first time.
8. Ask me before installing anything, creating accounts, or changing files outside this project folder.

## Progress

- **Milestone 1: done (Oct 24, 2026).** `server.py` has `fetch_feed()` and the `get_ai_news` tool. Repo: https://github.com/shreyad1/ai-brew
- **Milestone 2: done (Oct 24, 2026).** `sources.yaml` with sections `news`, `work`, `builder`, `longread`; sponsored filter (title, summary, categories); regex AI filter; headline dedupe (Jaccard 0.3); HTML-cleaned summaries capped at 500 chars. Tools: `get_ai_news`, `get_company_ai_updates`, `get_upcoming`, `get_dev_updates`, `get_long_reads`. Connected to Claude Desktop.
- **Design decided (Oct 24):** "The AI Brew", a newspaper + coffee-shop theme, quiet-luxury palette (ivory `#FBF8F3`, espresso `#2E2620`, muted gold `#B39060`, champagne `#F5EFE6`, sage `#EEF0EA`, blush `#F3E9E4`). Sections: Today's menu, The Big Pour (top news), Office Blend (AI at work), Still Roasting (coming up), Quick Sips (one-liners), The Builder's Bar (dark card for engineers: new tool, benchmark, trending concept picked from the week's news), Long Read (weekly Substack essay), Word of the Day, Keep Brewing (one resource to stay current), Tip Jar Poll. Plain-English subtitles for non-tech readers. Barista's Tip was dropped.
- **Shipped by Oct 24, 2026:** digest agent (Gemini + checks.py guardrails + one rewrite, then drop), daily GitHub Actions run, faithfulness evals (evals.py, LLM judge calibrated 14/14 on evals/judge_cases.yaml), 50 pytest tests + CI, interactive web app (Today / Events / Archive / Saved / #/trust) on **https://theaibrew.pages.dev** (Cloudflare Pages, deployed by pages.yml; old shreyad1.github.io/ai-brew forwards). Repo: https://github.com/shreyad1/ai-brew. Buttondown account `aibrew` awaiting review.
- **Open next:** prompt fixes from evals (concept definitions must come from the source; explainers keep qualifiers), refactor server.py into modules, docs/DESIGN.md, Buttondown sending once approved.
- **Next order:** email template (Jinja2) from the v4 design with one-click mailto poll buttons → Gemini writer with fact checks → interactive web edition on GitHub Pages → Buttondown sending → GitHub Actions.

**Setup notes:**

- `mcp` 2.3.0 is installed, so use `from mcp.server.mcpserver import MCPServer`.
- Flat project layout (no `[build-system]` in `pyproject.toml`).
- Stop the old MCP Inspector (Ctrl+C) before re-running `uv run mcp dev server.py`, or port 6274 stays in use.

## What we're building

**AI Brew**: a free daily email newsletter, in the style of IT Brew, written by an AI agent I build. Anyone (for example, my colleagues) can subscribe with their email.

Each issue covers:

1. **Top AI news**: the biggest AI stories of the day (model launches, funding, policy).
2. **AI at work**: how real companies are adopting AI (e.g., "Walmart uses AI agents for inventory"), with what it means for teams.
3. **Coming up**: upcoming launches, events, and announcements worth watching.
4. **Try it today**: one small, practical AI thing a reader can try in 5 minutes (e.g., a prompt to turn messy meeting notes into action items).
5. **Word of the day**: one AI term explained simply with a small everyday analogy. Words follow a **learning path**: each week has a theme and the words build on each other (e.g., Mon "LLM", Tue "token", Wed "context window", Thu "RAG", Fri "embedding").
6. **Quick poll**: one fun question readers answer by replying to the email (e.g., "Would you trust an AI agent to book your travel? Reply YES or NO"). The next issue shares the results.

Two parts, both open source:

- An **MCP (Model Context Protocol) server** that gives Claude or any MCP client tools to fetch AI news and company AI updates. Colleagues can plug it into Claude too.
- A **digest agent** that uses those tools every morning, picks and ranks stories, writes the issue, and sends it to subscribers.

Why it matters for hiring: it shows tool design for LLMs, working with real data sources, an agent that runs on its own, evals, and a product with real users.

## Tech stack

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) for the project, dependencies, and running
- MCP Python SDK: package `mcp[cli]` (2.x: `MCPServer`; 1.x: `FastMCP`)
- `httpx` for HTTP calls, `feedparser` for RSS feeds
- `pytest` + `pytest-asyncio` for tests
- LLM: start with the **Gemini API free tier** (no credit card needed). Keep the LLM call behind one small function so I can switch providers later.
- Newsletter delivery: **Buttondown** (free up to 100 subscribers; has a subscribe page and archive). Alternative if the list grows: **beehiiv** (free plan up to 2,500 subscribers). Check current limits and whether the API is available on the free plan before building Milestone 5.
- GitHub + GitHub Actions (free for public repos) to run the agent every morning

## Data sources (free)

Use **RSS feeds** only. Verify feed URLs before coding against them.

**Feed check, Oct 24, 2026 (re-verify before use):**

| Status | Feeds |
| --- | --- |
| In use (Milestone 1) | TechCrunch AI `https://techcrunch.com/category/artificial-intelligence/feed/`, Ars Technica AI `https://arstechnica.com/ai/feed/`, The Verge AI `https://www.theverge.com/rss/ai-artificial-intelligence/index.xml` |
| Working, add in Milestone 2 | MIT Tech Review AI `https://www.technologyreview.com/topic/artificial-intelligence/feed` (needs sponsored filter), ZDNet AI `https://www.zdnet.com/topic/artificial-intelligence/rss.xml`, Wired AI `https://www.wired.com/feed/tag/ai/latest/rss`, CIO.com `https://www.cio.com/feed/` (filter for AI), AWS ML blog `https://aws.amazon.com/blogs/machine-learning/feed/`, OpenAI News `https://openai.com/news/rss.xml`, Hugging Face `https://huggingface.co/blog/feed.xml`, Salesforce News `https://www.salesforce.com/news/feed/` |
| Not working | VentureBeat (429, stale, sponsored), Microsoft AI blog (403), Reuters (401), Anthropic `/rss.xml` (404), artificialintelligence-news.com (no items), Google AI blog (newest item Oct 13, stale) |
| Not available | IT Brew has no RSS feed (it does original reporting; AI Brew is a curator) |
| Later | Hacker News search API (`https://hn.algolia.com/api/v1/search`), only as a ranking signal, never as a source of facts |

- Drop **sponsored posts**: check title, summary, and categories for "Presented by", "Sponsored", "Partner content", "Insights", `sponsored`.
- Drop any feed whose newest item is older than 7 days, and log it.
- **Not used:** Twitter/X or any social media.

## Zero made-up content: the most important rule

AI Brew must never contain invented facts, numbers, quotes, dates, companies, or links. Every factual sentence must trace back to a real source item.

| Section | Source of truth | What the LLM may do |
| --- | --- | --- |
| Top stories, AI at work | Feed items (title, summary, link, date, publisher) | Choose items, rewrite the feed summary in plain words. Nothing beyond what the feed text says |
| Coming up | Feed items that mention an upcoming launch or event | Same. Show a date only if the source text states it; otherwise write "date not announced" |
| Try it today | My own reviewed list in `tips.yaml` | Pick one from the list. Never invent a new tip |
| Word of the day | My own reviewed glossary in `learning_path.yaml` | Copy the reviewed definition and analogy. "Used in a sentence" only by quoting or paraphrasing a real headline from today's items, with its link |
| Quick poll | Real email replies, counted by me in `polls.yaml` | Report the counted numbers exactly. If no results yet, say so |
| One-liner | Generated, clearly light-hearted | No facts, no numbers, no names |

**Guardrails in code (build in Milestone 3, test in Milestone 4):**

1. **Links:** every link in the issue must exactly match a link from the fetched feed items.
2. **Numbers:** every number in a summary must appear in that item's source title or summary. Otherwise regenerate or drop.
3. **Names:** every company or product name in a summary must appear in its source text.
4. **No quotes** unless copied exactly from the source text.
5. **Attribution:** every item shows its publisher and date, e.g., "— TechCrunch, Oct 23".
6. **Fail safe:** if checks fail twice for an item, drop it. If fewer than 3 good items remain, don't send; email me instead.
7. **Review mode on by default:** each issue goes to me first; subscribers only after I approve.
8. **Prompt rules:** the LLM gets only the source items, uses only that text, says "not stated in the source" instead of guessing, and returns structured JSON (item id + summary) so code assembles links and attributions.
9. **Log:** save each issue's source items and check results in `issues/YYYY-MM-DD.sources.json`.

**Content rules:** use only headline, short feed summary, and link; never republish full articles; summaries in our own words, always linking to the original; follow each site's feed terms; no scraping.

## MCP tools

| Tool | Inputs | Returns |
| --- | --- | --- |
| `get_ai_news` | `days: int = 1`, `limit: int = 20` | Recent AI stories: title, source, link, published date, short summary |
| `get_company_ai_updates` | `days: int = 3`, `company: str \| None = None`, `limit: int = 20` | Stories about companies adopting AI |
| `get_upcoming` | `days_ahead: int = 30` | Items mentioning launches or events coming up |
| `search_hn` (after Milestone 6) | `query: str`, `days: int = 7`, `limit: int = 10` | HN points and comment counts, only to boost ranking |

Rules for every tool: clear docstring; clamp inputs (e.g. `limit` 1–30); 10-second HTTP timeout; dedupe the same story across sites; on errors skip the broken feed and say which one failed, never crash.

## Milestones

1. **Setup + first tool** ✅
2. **AI at work + coming up:** company/industry feeds and `get_company_ai_updates`; `get_upcoming` with keyword filtering; dedupe similar headlines; connect to Claude Desktop (`uv run mcp install server.py`).
3. **Digest agent writes an issue:** `digest.py` calls the tools, the LLM picks and writes, output `issues/YYYY-MM-DD.md`. Never invent links or facts.
4. **Quality:** TTL cache; pytest with mocked HTTP; split into `feeds.py`, `tools.py`, `digest.py`, `llm.py`, `server.py`; README with screenshot.
5. **Subscribers + daily sending:** Buttondown/beehiiv with public subscribe page; send via API (or draft for review); GitHub Actions every weekday 7 AM Central; keys in GitHub secrets.
6. **Ship it:** evals for faithfulness and real links; review-mode switch; launch on LinkedIn; optional PyPI + MCP registry.

### Issue format (readable in 3 minutes)

```markdown
# AI Brew — Oct 24, 2026
**Subject: <a catchy one-liner about today's biggest story>**

Good morning! Here's what's brewing in AI today.

## Top stories
### 1. <Punchy headline>
<2-sentence summary in plain words.>
**Why it matters:** <one line.>
[Read more](link) — <Source name>

(3 top stories)

## AI at work
### <Company> is using AI to <do what>
<2 sentences: what they did and the result.>
**What it means for your team:** <one line.>
[Read more](link) — <Source name>

(2 company stories)

## Coming up
- <Upcoming launch or event, with date if known> — [link](link)
(2–3 items)

## Try it today
**<What to try, in a few words>**
<2–3 short steps a non-engineer can follow in 5 minutes, e.g., a copy-paste prompt.>

## Word of the day: <Term>
*This week's theme: <theme> (day <n> of 5)*
**Definition:** <one plain sentence.>
**Think of it like:** <a small everyday analogy.>
**Used in a sentence:** <one example from today's news, if possible.>
**Builds on:** <yesterday's word, and how they connect.>

## Quick poll
<One fun question.> Reply **YES** or **NO**. Results in the next issue.
<Yesterday's results, if any.>

## One-liner
<A light, fun closing line.>

---
You're receiving AI Brew because you subscribed. Unsubscribe anytime.
```

**Writing rules:** conversational but accurate; no hype words; every claim from the source text; if unsure, say so. "Try it today" tips must be safe and free, and never ask readers to paste private or work-confidential data into AI tools.

**Learning path:** `learning_path.yaml` with weekly themes (e.g., "How LLMs work", "Building with AI", "AI agents", "AI safety and trust"), 5 words each in order, plus a record of used words.

**Polls:** I count email replies by hand into `polls.yaml`; automate later (optional).

### Email design: pastel sections

| Section | Colour | Hex |
| --- | --- | --- |
| Header / masthead | Soft lilac | `#F3EEFB` |
| Top stories | Lavender | `#EDE7F6` |
| AI at work | Mint | `#E3F4EC` |
| Coming up | Peach | `#FDEBDD` |
| Try it today | Sky blue | `#E3F0FB` |
| Word of the day | Butter yellow | `#FFF6D6` |
| Quick poll + one-liner | Blush pink | `#FCE4EC` |

Inline styles and `<table>` layout only; text `#1F2937`, links `#4338CA`; single column ~600 px; font `-apple-system, Segoe UI, Roboto, Arial, sans-serif`, 16 px; Jinja2 template plus a plain-text version; check the platform's custom HTML support before Milestone 5; test in Gmail and Outlook on phone and laptop.

## Target structure

```
ai-brew/
├── server.py          # MCP server: registers the tools
├── feeds.py           # fetching and cleaning RSS feeds
├── tools.py           # tool logic (news, company updates, upcoming)
├── llm.py             # one small wrapper around the LLM API
├── digest.py          # builds and sends the daily issue
├── sources.yaml       # list of feeds by section
├── learning_path.yaml # reviewed glossary
├── tips.yaml          # reviewed "Try it today" tips
├── checks.py          # guardrails: link, number, and name checks
├── polls.yaml         # poll questions and results
├── templates/email.html.j2
├── issues/
├── tests/
├── .github/workflows/daily.yml
├── pyproject.toml
├── README.md
└── .gitignore
```

## Costs: keep it at $0

GitHub repo + Actions (free for public), Gemini free tier, Buttondown free up to 100 subscribers (beehiiv up to 2,500). Optional later: custom domain.

## Code style

- Type hints on all functions
- Small functions with one job each
- Comments only where the "why" isn't obvious
- No secrets in code. API keys go in `.env`, listed in `.gitignore`

## Start of every session

Ask me which milestone we're on and what I finished last time. Then begin with the first small step.
