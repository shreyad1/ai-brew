// The AI Brew web app: one page, four tabs (Today, Events, Archive, Saved), hash-based routing.
// All data ships inside the page (#app-data), so it works offline and when opened from disk.

const DATA = JSON.parse(document.getElementById("app-data").textContent);
const ISSUES = DATA.issues; // newest first
const PICKS = DATA.events.picks || {};
const view = document.getElementById("view");

// ---------- small helpers ----------

const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = {
  get(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage blocked */ } },
};
const when = (iso) => new Date(iso).toLocaleString(undefined, { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
const issueNo = (n) => String(n).padStart(3, "0");

// ---------- saved stories ----------

let saved = store.get("aibrew-saved", {});

function updateSavedBadge() {
  const count = Object.keys(saved).length;
  const badge = document.getElementById("saved-count");
  badge.textContent = count;
  badge.hidden = count === 0;
}

function toggleSave(story, issue) {
  if (saved[story.link]) delete saved[story.link];
  else saved[story.link] = { headline: story.headline || story.summary, summary: story.headline ? story.summary : "", link: story.link, source: story.source, date: issue.date_long, savedAt: Date.now() };
  store.set("aibrew-saved", saved);
  updateSavedBadge();
}

const saveButton = (story) => `<button type="button" class="save" data-save="${esc(story.link)}" aria-pressed="${Boolean(saved[story.link])}" aria-label="${saved[story.link] ? "Remove from saved" : "Save story"}">${saved[story.link] ? "&#9733;" : "&#9734;"}</button>`;

// ---------- the cup ----------
// A blue-and-white ceramic cup on a saucer, drawn from simple shapes. Colours come from CSS tokens.
const CUP = `<svg class="cup" viewBox="0 0 160 150" role="img" aria-label="A cup of coffee">
  <g class="steam" fill="none" stroke-linecap="round" stroke-width="3">
    <path d="M62 42 C 54 32, 70 26, 62 14" />
    <path d="M80 40 C 72 28, 90 22, 80 6" />
    <path d="M98 42 C 90 32, 106 26, 98 14" />
  </g>
  <ellipse class="saucer" cx="80" cy="132" rx="66" ry="12" />
  <ellipse class="saucer-well" cx="80" cy="129" rx="40" ry="6" />
  <path class="handle" d="M122 72 C 146 72, 146 108, 118 106" fill="none" stroke-width="9" stroke-linecap="round" />
  <path class="body" d="M34 58 H126 L120 112 C 118 122, 108 128, 96 128 H64 C 52 128, 42 122, 40 112 Z" />
  <path class="band" d="M36.6 76 H123.4 L122.3 86 H37.7 Z" />
  <g class="dots"><circle cx="56" cy="100" r="3" /><circle cx="72" cy="104" r="3" /><circle cx="88" cy="104" r="3" /><circle cx="104" cy="100" r="3" /></g>
  <ellipse class="rim" cx="80" cy="58" rx="46" ry="9" />
  <ellipse class="coffee" cx="80" cy="59" rx="40" ry="6.5" />
  <path class="crema" d="M66 59 C 72 55, 88 55, 94 59 C 88 62, 72 62, 66 59 Z" />
</svg>`;

// ---------- pieces of an issue ----------

const photo = (story) => story.image
  ? `<figure class="photo"><a href="${esc(story.link)}" tabindex="-1"><img src="${esc(story.image)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.closest('figure').remove()"></a><figcaption>Image: ${esc(story.source)}</figcaption></figure>`
  : "";

const meta = (story) => `<div class="meta"><a href="${esc(story.link)}">Read at ${esc(story.source)} &rarr;</a>${saveButton(story)}</div>`;

const section = (id, name, body, extraClass = "") => `
  <section class="section ${extraClass}" id="${id}">
    <div class="rail"><h2>${esc(name)}</h2></div>
    <div class="content">${body}</div>
  </section>`;

function storyBlock(story, { lead = false, withPhoto = true, label = "" } = {}) {
  let text = `<p>${esc(story.summary)}</p>`;
  if (lead && story.explain) {
    const versions = [["standard", "The short version", story.summary], ["kid", "Like I'm 10"], ["pm", "Like a PM"], ["engineer", "Like an engineer"]]
      .map(([key, name, fixed]) => [key, name, fixed ?? story.explain[key]])
      .filter(([, , value]) => value);
    text = `<div class="explain">
      <div class="explain-tabs" role="tablist" aria-label="Explain it like">${versions.map(([key, name], i) => `<button type="button" role="tab" aria-selected="${i === 0}" data-version="${key}">${name}</button>`).join("")}</div>
      ${versions.map(([key, , value], i) => `<p data-version="${key}"${i ? " hidden" : ""}>${esc(value)}</p>`).join("")}
    </div>`;
  }
  return `<article class="story${lead ? " lead" : ""}">
    ${withPhoto ? photo(story) : ""}
    ${label ? `<span class="label">${esc(label)}</span>` : ""}
    <h3>${esc(story.headline)}</h3>
    ${text}
    ${lead && story.why ? `<div class="why"><b>Why you should care</b>${esc(story.why)}</div>` : ""}
    ${meta(story)}
  </article>`;
}

function renderIssue(issue) {
  const parts = [];
  parts.push(`<header class="issue-head">
    <div class="masthead">
      <h1 class="wordmark">The AI <em>Brew</em></h1>
      ${CUP}
      <div class="stamp"><b>No. ${issueNo(issue.number)}</b>${esc(issue.date_long)}</div>
    </div>
  </header>`);

  if ((issue.glance || []).length) parts.push(`<section class="glance" id="at-a-glance" data-open="false">
    <button type="button" class="glance-toggle" aria-expanded="false" aria-controls="glance-body-${esc(issue.date_iso)}">
      <span class="glance-cup" aria-hidden="true">&#9749;</span>
      <span class="glance-title">At a glance</span>
      <span class="glance-meta">${issue.glance.length} stories &middot; 30-second read</span>
      <span class="glance-chevron" aria-hidden="true"></span>
    </button>
    <div class="glance-body" id="glance-body-${esc(issue.date_iso)}"><div class="glance-inner">
      <ul>${issue.glance.map((g, i) => `<li style="--i:${i}"><span>${esc(g.summary)}</span> <a href="${esc(g.link)}">${esc(g.source)}</a></li>`).join("")}</ul>
    </div></div>
  </section>`);

  const pour = issue.big_pour || [];
  if (pour.length) {
    const pair = pour.slice(1, 3);
    const pairPhotos = pair.every((s) => s.image);
    parts.push(section("the-big-pour", "The Big Pour", `
      ${storyBlock(pour[0], { lead: true })}
      ${pair.length ? `<div class="pair-stories">${pair.map((s) => storyBlock(s, { withPhoto: pairPhotos })).join("")}</div>` : ""}`));
  }

  const builder = issue.builder || {};
  if ((builder.stories || []).length || builder.concept) {
    const concept = builder.concept ? `<div class="card" data-open="false">
        <span class="label">Concept to know</span><span class="term">${esc(builder.concept.term)}</span>
        <button type="button" class="reveal" aria-expanded="false">What does it mean?</button>
        <div class="hidden-part"><p class="def">${esc(builder.concept.explanation)}</p></div></div>` : "";
    parts.push(section("the-builders-bar", "The Builder's Bar", (builder.stories || []).map((s) => storyBlock(s, { label: s.label })).join("") + concept, "night"));
  }

  if ((issue.office_blend || []).length) parts.push(section("office-blend", "Office Blend", issue.office_blend.map((s) => storyBlock(s)).join("")));

  if ((issue.still_roasting || []).length) parts.push(section("still-roasting", "Still Roasting", `<ul class="list">${issue.still_roasting.map((item, i) => `
    <li><span class="n">${String(i + 1).padStart(2, "0")}</span><div><p>${esc(item.summary)}</p>
    <span class="when">${esc(item.date_mentioned || "Date not announced")} &middot; <a href="${esc(item.link)}">${esc(item.source)}</a></span></div></li>`).join("")}</ul>`));

  if ((issue.quick_sips || []).length) parts.push(section("quick-sips", "Quick Sips", `<ul class="list">${issue.quick_sips.map((sip) => `
    <li><span class="n">&mdash;</span><div><p>${esc(sip.summary)}</p><span class="when"><a href="${esc(sip.link)}">${esc(sip.source)}</a> ${saveButton(sip)}</span></div></li>`).join("")}</ul>`));

  if (issue.long_read) parts.push(section("the-long-read", "The Long Read", storyBlock(issue.long_read, { withPhoto: false, label: `from ${issue.long_read.source}` })));

  const cards = [];
  if (issue.word) cards.push(`<div class="card" data-open="false">
    <span class="label">Word of the day &middot; ${esc(issue.word.theme)}, ${esc(issue.word.day)} of 5</span>
    <span class="term">${esc(issue.word.term)}</span>
    ${(window.ILLUSTRATIONS || {})[issue.word.term.toLowerCase()] ? `<figure class="explainer">${window.ILLUSTRATIONS[issue.word.term.toLowerCase()]}</figure>` : ""}
    ${issue.word.heard ? `<p class="heard"><span>Heard at work</span>${esc(issue.word.heard)}</p>` : ""}
    <button type="button" class="reveal" aria-expanded="false">Reveal the meaning</button>
    <div class="hidden-part"><p>${esc(issue.word.definition)}</p><p class="def">${esc(issue.word.analogy)}</p></div></div>`);
  if (issue.keep_brewing) cards.push(`<div class="card"><span class="label">Keep brewing</span>
    <span class="term small">${esc(issue.keep_brewing.name)}</span><p class="def">${esc(issue.keep_brewing.description)}</p>
    <a href="${esc(issue.keep_brewing.link)}">Start here &rarr;</a></div>`);
  if (cards.length) parts.push(section("learn", "Learn", `<div class="cards">${cards.join("")}</div>`));

  if (issue.poll) parts.push(section("poll", "Tip Jar Poll", `
    ${issue.poll.last_results ? `<p class="mono">Last time: ${esc(issue.poll.last_results)}</p>` : ""}
    <p class="question">${esc(issue.poll.question)}</p>
    <div class="vote">${["YES", "NO"].map((a) => `<a href="mailto:${esc(issue.reply_to)}?subject=${encodeURIComponent(`Poll ${issue.date_iso}: ${a}`)}">${a}</a>`).join("")}</div>`));

  parts.push(`<section class="section" id="subscribe">
    <div class="rail"><h2>Get it by email</h2></div>
    <div class="content">
      <p>The AI Brew in your inbox every morning. Free, and you can unsubscribe anytime.</p>
      <form class="signup" action="https://buttondown.com/api/emails/embed-subscribe/deshpande" method="post" target="_blank">
        <label for="email-${esc(issue.date_iso)}" class="visually-hidden">Email address</label>
        <input id="email-${esc(issue.date_iso)}" type="email" name="email" placeholder="you@example.com" required>
        <button type="submit">Subscribe</button>
      </form>
    </div>
  </section>`);
  parts.push(`<p class="quiet-link"><a href="#/trust">How we fact-check</a></p>`);
  return parts.join("");
}

// ---------- views ----------

function viewToday() { return ISSUES.length ? renderIssue(ISSUES[0]) : `<p class="empty">The first issue is still brewing.</p>`; }

function viewIssue(date) {
  const issue = ISSUES.find((i) => i.date_iso === date);
  return issue ? `<a class="back" href="#/archive">&larr; Archive</a>${renderIssue(issue)}` : `<p class="empty">No issue for ${esc(date)}. <a href="#/archive">See the archive</a>.</p>`;
}

function viewEvents() {
  return `<div class="page-head"><h1 class="page-title">AI events near you</h1>
    <p class="page-sub">Meetups, hackathons, and talks in the next 30 days, from Luma.</p></div>
    <div class="picker">${document.getElementById("places-template").innerHTML}</div>
    <p class="events-note" id="events-note" hidden></p>
    <ul class="list events" id="events-list"></ul>
    <p class="empty" id="events-empty"></p>`;
}

function renderEvents(place) {
  const list = document.getElementById("events-list");
  const note = document.getElementById("events-note");
  const empty = document.getElementById("events-empty");
  list.replaceChildren();
  note.hidden = true;
  empty.hidden = false;
  if (!place) { empty.textContent = "Pick a state or city to see what's coming up."; return; }
  const pick = PICKS[place];
  if (!pick) { empty.textContent = "Events couldn't be loaded. Try again tomorrow."; return; }
  if (pick.note) { note.textContent = pick.note; note.hidden = false; }
  if (!pick.events.length) { empty.textContent = `No AI events listed near ${pick.label} in the next 30 days.`; return; }
  empty.hidden = true;
  list.innerHTML = pick.events.map((e, i) => `<li><span class="n">${String(i + 1).padStart(2, "0")}</span>
    <div><a class="event-title" href="${esc(e.link)}">${esc(e.title)}</a>
    <span class="when">${esc(when(e.start))} &middot; ${esc(e.venue)} &middot; ${esc(e.city)}</span></div></li>`).join("");
}

// Every story across every issue, for search.
const ALL_STORIES = ISSUES.flatMap((issue) => {
  const stories = [
    ...(issue.big_pour || []), ...(issue.office_blend || []), ...(issue.quick_sips || []),
    ...((issue.builder || {}).stories || []), ...(issue.long_read ? [issue.long_read] : []),
  ];
  return stories.map((s) => ({ ...s, issue }));
});

function viewArchive() {
  return `<div class="page-head"><h1 class="page-title">Archive</h1>
    <p class="page-sub">${ISSUES.length} issue${ISSUES.length === 1 ? "" : "s"} so far. Search every story.</p></div>
    <label for="search" class="visually-hidden">Search stories</label>
    <input id="search" class="search" type="search" placeholder="Search: OpenAI, agents, Pennsylvania&hellip;" autocomplete="off">
    <div id="results"></div>`;
}

function renderArchive(query) {
  const results = document.getElementById("results");
  const q = query.trim().toLowerCase();
  if (!q) {
    results.innerHTML = `<ul class="issues">${ISSUES.map((i) => `<li><a href="#/issue/${esc(i.date_iso)}">
      <span class="mono">No. ${issueNo(i.number)}<br>${esc(i.date_long)}</span>
      <div><h3>${esc(i.big_pour?.[0]?.headline || "The AI Brew")}</h3><p>${esc(i.big_pour?.[0]?.summary || "")}</p></div></a></li>`).join("")}</ul>`;
    return;
  }
  const hits = ALL_STORIES.filter((s) => `${s.headline || ""} ${s.summary} ${s.source}`.toLowerCase().includes(q));
  results.innerHTML = hits.length
    ? `<p class="mono">${hits.length} stor${hits.length === 1 ? "y" : "ies"}</p><ul class="list">${hits.map((s) => `<li><span class="n">&mdash;</span><div>
        <a class="event-title" href="${esc(s.link)}">${esc(s.headline || s.summary)}</a>
        <span class="when">${esc(s.source)} &middot; <a href="#/issue/${esc(s.issue.date_iso)}">${esc(s.issue.date_long)}</a> ${saveButton(s)}</span></div></li>`).join("")}</ul>`
    : `<p class="empty">No stories match &ldquo;${esc(query)}&rdquo;.</p>`;
}

function viewSaved() {
  const items = Object.values(saved).sort((a, b) => b.savedAt - a.savedAt);
  return `<div class="page-head"><h1 class="page-title">Saved</h1>
    <p class="page-sub">Stories you starred. Kept in this browser only.</p></div>
    ${items.length ? `<ul class="list">${items.map((s) => `<li><span class="n">&#9733;</span><div>
      <a class="event-title" href="${esc(s.link)}">${esc(s.headline)}</a>
      ${s.summary ? `<p>${esc(s.summary)}</p>` : ""}
      <span class="when">${esc(s.source)} &middot; ${esc(s.date)} ${saveButton(s)}</span></div></li>`).join("")}</ul>`
      : `<p class="empty">Nothing saved yet. Tap &#9734; next to any story to keep it here.</p>`}`;
}

function viewTrust() {
  const trust = DATA.trust || {};
  const history = [...(trust.history || [])].reverse();
  const cal = trust.calibration;
  const latest = ISSUES.find((i) => i.eval);
  const pct = (x) => (x == null ? "–" : `${Math.round(x * 100)}%`);
  return `<div class="page-head"><h1 class="page-title">How we fact-check</h1>
    <p class="page-sub">Every sentence the AI writes is checked twice: by code, then by a second AI acting as a strict fact-checker.</p></div>
    <section class="section"><div class="rail"><h2>The checks</h2></div><div class="content">
      <ul class="list">
        <li><span class="n">01</span><div><p><b>Code checks.</b> Every number, name, and quote must appear in the story's source. Failing lines get one rewrite, then they're dropped.</p></div></li>
        <li><span class="n">02</span><div><p><b>AI judge.</b> A separate, stronger model reads each sentence next to its source and labels it supported, partly supported, or unsupported.</p></div></li>
        <li><span class="n">03</span><div><p><b>The links are never written by the AI.</b> Code attaches every link and source name from the original feed.</p></div></li>
      </ul></div></section>
    <section class="section"><div class="rail"><h2>Scores</h2></div><div class="content">
      ${history.length ? `<table class="scores"><thead><tr><th>Issue</th><th>Sentences</th><th>Supported</th><th>Partly</th><th>Unsupported</th><th>Score</th></tr></thead><tbody>
        ${history.map((h) => `<tr><td><a href="#/issue/${esc(h.date)}">${esc(h.date)}</a></td><td>${h.claims}</td><td>${h.supported}</td><td>${h.partial}</td><td>${h.unsupported}</td><td><b>${pct(h.faithfulness)}</b></td></tr>`).join("")}
      </tbody></table>` : `<p class="empty">No scores yet.</p>`}
    </div></section>
    ${latest && latest.eval.flagged.length ? `<section class="section"><div class="rail"><h2>Flagged in the latest issue</h2></div><div class="content"><ul class="list">
      ${latest.eval.flagged.map((f) => `<li><span class="n tag-${esc(f.verdict)}">${f.verdict === "partial" ? "partly" : "no"}</span><div><p>&ldquo;${esc(f.claim)}&rdquo;</p><span class="when">${esc(f.reason)}</span></div></li>`).join("")}
    </ul></div></section>` : ""}
    ${cal ? `<section class="section"><div class="rail"><h2>Checking the checker</h2></div><div class="content">
      <p>We tested the AI judge on ${cal.cases} sentences a person had already labelled, including planted mistakes.</p>
      <ul class="list"><li><span class="n">&#10003;</span><div><p>Caught <b>${esc(cal.errors_caught)}</b> planted or partial errors</p></div></li>
      <li><span class="n">!</span><div><p>False alarms on correct sentences: <b>${esc(cal.false_alarms)}</b></p></div></li>
      <li><span class="n">=</span><div><p>Exact agreement with the human label: <b>${pct(cal.exact_agreement)}</b></p></div></li></ul>
    </div></section>` : ""}`;
}

// ---------- router ----------

function route() {
  const [, tab = "today", arg] = location.hash.split("/");
  const views = { today: viewToday, events: viewEvents, archive: viewArchive, saved: viewSaved, trust: viewTrust, issue: () => viewIssue(arg) };
  view.innerHTML = (views[tab] || viewToday)();
  document.querySelectorAll(".tabs a").forEach((a) => a.setAttribute("aria-current", String(a.dataset.tab === (tab === "issue" ? "archive" : tab))));

  if (tab === "events") {
    const picker = document.getElementById("place-picker");
    picker.value = store.get("aibrew-place", "");
    picker.addEventListener("change", () => { store.set("aibrew-place", picker.value); renderEvents(picker.value); });
    renderEvents(picker.value);
  }
  if (tab === "archive") {
    const search = document.getElementById("search");
    search.addEventListener("input", () => renderArchive(search.value));
    renderArchive("");
  }
  window.scrollTo(0, 0);
}

// One click handler for everything inside the view.
view.addEventListener("click", (event) => {
  const save = event.target.closest("button.save");
  if (save) {
    const story = ALL_STORIES.find((s) => s.link === save.dataset.save) || saved[save.dataset.save];
    toggleSave(story, story.issue || { date_long: story.date });
    const on = Boolean(saved[save.dataset.save]);
    document.querySelectorAll(`button.save[data-save="${CSS.escape(save.dataset.save)}"]`).forEach((b) => {
      b.setAttribute("aria-pressed", String(on));
      b.setAttribute("aria-label", on ? "Remove from saved" : "Save story");
      b.innerHTML = on ? "&#9733;" : "&#9734;";
    });
    if (location.hash === "#/saved") route();
    return;
  }
  const tab = event.target.closest(".explain-tabs button");
  if (tab) {
    const box = tab.closest(".explain");
    box.querySelectorAll(".explain-tabs button").forEach((t) => t.setAttribute("aria-selected", String(t === tab)));
    box.querySelectorAll("p[data-version]").forEach((p) => { p.hidden = p.dataset.version !== tab.dataset.version; });
    return;
  }
  const glance = event.target.closest(".glance-toggle");
  if (glance) {
    const box = glance.closest(".glance");
    const open = box.dataset.open !== "true";
    box.dataset.open = String(open);
    glance.setAttribute("aria-expanded", String(open));
    return;
  }
  const reveal = event.target.closest(".card .reveal");
  if (reveal) {
    const card = reveal.closest(".card");
    const open = card.dataset.open !== "true";
    card.dataset.open = String(open);
    reveal.setAttribute("aria-expanded", String(open));
    reveal.dataset.closedLabel ??= reveal.textContent;
    reveal.textContent = open ? "Hide" : reveal.dataset.closedLabel;
  }
});

// ---------- theme ----------

const themeButton = document.getElementById("theme-toggle");
const isDark = () => (document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark";
const themeLabel = () => themeButton.setAttribute("aria-label", isDark() ? "Switch to light theme" : "Switch to dark theme");
themeButton.addEventListener("click", () => {
  const next = isDark() ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("aibrew-theme", next); } catch { /* storage blocked */ }
  themeLabel();
});
themeLabel();

updateSavedBadge();
window.addEventListener("hashchange", route);
route();
