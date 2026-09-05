// Molt dev console — tiny tab router. No framework, no build step.
// Each panel module in ./panels/*.js exports an async `render(root)` function
// that owns its own fetch + DOM. Panels are loaded lazily on first visit and
// cached in `loaded` so switching tabs doesn't re-fetch every time.

const PANELS = {
  candidates: () => import("./panels/candidates.js"),
  repoStatus: () => import("./panels/repoStatus.js"),
  ruleViewer: () => import("./panels/ruleViewer.js"),
  diffPreview: () => import("./panels/diffPreview.js"),
  verification: () => import("./panels/verification.js"),
  llmAttempts: () => import("./panels/llmAttempts.js"),
  costUsage: () => import("./panels/costUsage.js"),
  logs: () => import("./panels/logs.js"),
};

const root = document.getElementById("panel-root");
const tabs = document.querySelectorAll(".tab");
const loaded = new Set();

async function showPanel(name) {
  tabs.forEach((t) => t.classList.toggle("active", t.dataset.panel === name));

  const containerId = `panel-${name}`;
  let container = document.getElementById(containerId);

  if (!container) {
    root.innerHTML = "";
    container = document.createElement("div");
    container.id = containerId;
    root.appendChild(container);
  } else {
    Array.from(root.children).forEach((c) => (c.hidden = c.id !== containerId));
  }

  if (loaded.has(name)) return;
  loaded.add(name);

  container.innerHTML = `<p class="loading">Loading ${name}…</p>`;
  try {
    const mod = await PANELS[name]();
    await mod.render(container);
  } catch (err) {
    console.error(`Panel "${name}" failed to render`, err);
    container.innerHTML = `<div class="error-box"><strong>Panel failed to load.</strong><br>${escapeHtml(
      String(err && err.stack ? err.stack : err)
    )}<br><br>If this is a "Failed to fetch" error, the console likely needs to be served over HTTP rather than opened as a file:// URL — see console/README.md.</div>`;
    loaded.delete(name); // allow retry on next click
  }
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => showPanel(tab.dataset.panel));
});

// Deep-link support: #ruleViewer opens that tab directly.
const initial = location.hash.replace("#", "");
showPanel(PANELS[initial] ? initial : "candidates");
