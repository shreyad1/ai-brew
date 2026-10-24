// The AI Brew web edition: audience toggle and reveal cards.

const AUDIENCE_KEY = "aibrew-audience";

function readAudience() {
  try { return localStorage.getItem(AUDIENCE_KEY) || "everyone"; } catch { return "everyone"; }
}

function setAudience(audience) {
  document.body.dataset.audience = audience;
  document.querySelectorAll("button[data-audience]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.audience === audience));
  });
  try { localStorage.setItem(AUDIENCE_KEY, audience); } catch { /* private mode: just don't remember */ }
}

document.querySelectorAll("button[data-audience]").forEach((button) => {
  button.addEventListener("click", () => setAudience(button.dataset.audience));
});
setAudience(readAudience());

document.querySelectorAll(".card .reveal").forEach((button) => {
  const card = button.closest(".card");
  const closedLabel = button.textContent;
  button.addEventListener("click", () => {
    const open = card.dataset.open !== "true";
    card.dataset.open = String(open);
    button.setAttribute("aria-expanded", String(open));
    button.textContent = open ? "Hide" : closedLabel;
  });
});

// Near You: AI events for the reader's state or city, from events.json (rebuilt every morning).
const PLACE_KEY = "aibrew-place";
const picker = document.getElementById("place-picker");

if (picker) {
  const list = document.getElementById("events-list");
  const note = document.getElementById("events-note");
  const empty = document.getElementById("events-empty");
  const eventsUrl = new URL("events.json", document.currentScript?.src || location.href);
  let picks = null;

  const when = (iso) => new Date(iso).toLocaleString(undefined, {
    weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });

  function render(place) {
    list.replaceChildren();
    note.hidden = true;
    if (!place) { empty.hidden = false; empty.textContent = "Pick a place to see upcoming AI meetups, hackathons, and talks. Listings come from Luma."; return; }
    const pick = picks && picks[place];
    if (!pick) { empty.hidden = false; empty.textContent = "Events couldn't be loaded right now. Try again later."; return; }
    if (pick.note) { note.textContent = pick.note; note.hidden = false; }
    if (!pick.events.length) { empty.hidden = false; empty.textContent = `No AI events listed near ${pick.label} in the next 30 days.`; return; }
    empty.hidden = true;
    pick.events.forEach((event, i) => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="n">${String(i + 1).padStart(2, "0")}</span><div><a class="event-title"></a><span class="when"></span></div>`;
      const link = li.querySelector("a");
      link.href = event.link;
      link.textContent = event.title;
      li.querySelector(".when").textContent = `${when(event.start)} · ${event.venue} · ${event.city}`;
      list.append(li);
    });
  }

  fetch(eventsUrl)
    .then((response) => response.json())
    .then((data) => { picks = data.picks; render(picker.value); })
    .catch(() => { picks = {}; render(picker.value); });

  try { picker.value = localStorage.getItem(PLACE_KEY) || ""; } catch { /* storage blocked */ }
  picker.addEventListener("change", () => {
    try { localStorage.setItem(PLACE_KEY, picker.value); } catch { /* storage blocked */ }
    render(picker.value);
  });
}
