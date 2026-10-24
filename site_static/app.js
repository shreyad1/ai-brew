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
