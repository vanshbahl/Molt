import { fetchJson, escapeHtml, badge, calloutRealSection, calloutMockSection } from "./_util.js";

export async function render(root) {
  const [rawLogRes, mock] = await Promise.all([
    fetch("../../experiments/probe_logs.txt"),
    fetchJson("./mock/logs.json"),
  ]);
  const rawLog = rawLogRes.ok ? await rawLogRes.text() : "(could not load experiments/probe_logs.txt)";

  root.innerHTML = `
    <h1>Raw Logs / Errors</h1>

    <h2>M0 feasibility probe output ${badge("real", "real")}</h2>
    ${calloutRealSection(
      "Actual captured terminal output",
      "Raw stdout from the venv probes behind the Repo/Test Status panel — not summarized, not invented."
    )}
    <pre class="json-view">${escapeHtml(rawLog)}</pre>

    <h2>Harness log (future)</h2>
    ${calloutMockSection(
      "No CLI, verification, or repair process exists",
      "These lines only show the intended shape (info/warn/error, source module, message) — nothing produced them."
    )}
    <table>
      <thead><tr><th>Level</th><th>Source</th><th>Message</th></tr></thead>
      <tbody>
        ${mock.entries
          .map(
            (e) => `<tr>
              <td><span class="tag ${levelClass(e.level)}">${escapeHtml(e.level)}</span></td>
              <td>${escapeHtml(e.source)}</td>
              <td>${escapeHtml(e.message)}</td>
            </tr>`
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function levelClass(level) {
  if (level === "error") return "tag-fail";
  if (level === "warn") return "tag-mixed";
  return "";
}
