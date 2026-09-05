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
  const cls = { real: "badge-real", mock: "badge-mock", partial: "badge-partial" }[kind] || "badge-mock";
  return `<span class="badge ${cls}">${escapeHtml(label || kind)}</span>`;
}

export function calloutRealSection(title, note) {
  return `<div class="callout">${badge("real", "real")} <strong>${escapeHtml(title)}</strong><br>${escapeHtml(note)}</div>`;
}

export function calloutMockSection(title, note) {
  return `<div class="callout">${badge("mock", "mock / not implemented")} <strong>${escapeHtml(title)}</strong><br>${escapeHtml(note)}</div>`;
}

export function pretty(obj) {
  return escapeHtml(JSON.stringify(obj, null, 2));
}
