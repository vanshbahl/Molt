import { fetchJson, escapeHtml, calloutRealSection, pretty } from "./_util.js";

export async function render(root) {
  const [rule, schema] = await Promise.all([
    fetchJson("./data/pyjwt_manual_rule.json"),
    fetchJson("./data/rule_schema.json"),
  ]);

  root.innerHTML = `
    <h1>Rule JSON / Schema Viewer</h1>
    <p class="panel-intro">Canonical rule language <code>molt.rule.v2</code> (DOCS/RULE_SPEC.md), validated by <code>src/molt/schema.py</code>.</p>

    <h2>PyJWT manual reference rule</h2>
    ${calloutRealSection(
      "Real, validated, executed by the engine — hand-written, not LLM output",
      "migrations/pyjwt-1-to-2/rule.json. Passes JSON Schema + semantic validation and is the rule behind the Transform Diff panel's engine result."
    )}
    <table>
      <thead><tr><th>#</th><th>op</th><th>id</th><th>target</th></tr></thead>
      <tbody>
        ${rule.operations
          .map(
            (op, i) => `<tr><td>${i + 1}</td><td><span class="tag">${escapeHtml(op.op)}</span></td><td>${escapeHtml(op.id)}</td><td>${escapeHtml(
              op.qualified_old_name ? `${op.qualified_old_name} → ${op.qualified_new_name}` : op.target_call || ""
            )}</td></tr>`
          )
          .join("")}
      </tbody>
    </table>
    <pre class="json-view">${pretty(rule)}</pre>

    <h2>JSON Schema (experiments/rule_schema.json)</h2>
    ${calloutRealSection("Registered structural schema", "Draft 2020-12. Semantic checks (unique ids, no rename chains, trigger/edit consistency, version ranges) live in src/molt/schema.py.")}
    <pre class="json-view">${pretty(schema)}</pre>
  `;
}
