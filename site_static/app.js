// The AI Brew web edition: audience toggle and flip cards.

const AUDIENCE_KEY = "aibrew-audience";

function readAudience() {
  try { return localStorage.getItem(AUDIENCE_KEY) || "everyone"; } catch { return "everyone"; }
}

function setAudience(audience) {
  document.body.dataset.audience = audience;
  document.querySelectorAll("[data-audience]").forEach((button) => {
    if (button.tagName === "BUTTON") button.setAttribute("aria-pressed", String(button.dataset.audience === audience));
  });
  try { localStorage.setItem(AUDIENCE_KEY, audience); } catch { /* private mode: just don't remember */ }
}

document.querySelectorAll("button[data-audience]").forEach((button) => {
  button.addEventListener("click", () => setAudience(button.dataset.audience));
});
setAudience(readAudience());

document.querySelectorAll(".flip").forEach((card) => {
  card.addEventListener("click", () => card.classList.toggle("flipped"));
});
