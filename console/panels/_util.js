// Shared helpers for console panels. Deliberately tiny — this is a dev
// console, not a component framework.

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

export async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Fetch failed for ${path}: HTTP ${res.status}`);
  return res.json();
}

export function badge(kind, label) {
  const cls = { real: "badge-real", mock: "badge-mock", partial: "badge-partial", estimate: "badge-estimate" }[kind] || "badge-mock";
  return `<span class="badge ${cls}">${escapeHtml(label || kind)}</span>`;
}

export function calloutRealSection(title, note) {
  return `<div class="callout">${badge("real", "real")} <strong>${escapeHtml(title)}</strong><br>${escapeHtml(note)}</div>`;
}

export function calloutMockSection(title, note) {
  return `<div class="callout">${badge("mock", "mock / not implemented")} <strong>${escapeHtml(title)}</strong><br>${escapeHtml(note)}</div>`;
}

// A third state, distinct from "real" (measured) and "mock" (placeholder, no
// module exists): a genuine M0 artifact (real evidence-packet size, real
// dated price schedule) run through a disclosed, labeled projection method.
// Never a billed/observed number. See experiments/pilot_estimate.json.
export function calloutEstimateSection(title, note) {
  return `<div class="callout">${badge("estimate", "estimate / projection, not measured")} <strong>${escapeHtml(title)}</strong><br>${escapeHtml(note)}</div>`;
}

export function pretty(obj) {
  return escapeHtml(JSON.stringify(obj, null, 2));
}
