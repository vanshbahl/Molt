import { fetchJson, calloutMockSection, pretty } from "./_util.js";

export async function render(root) {
  const schema = await fetchJson("./mock/rule_schema.json");

  root.innerHTML = `
    <h1>Rule JSON / Schema Viewer</h1>
    <p class="panel-intro">Will eventually render <code>rules/schema.py</code>'s exported JSON Schema and validated rule bundles (Phase 1). For now this is a raw JSON viewer over a hand-written illustration.</p>
    ${calloutMockSection(
      "Nothing here is a real schema",
      "No rule schema, validator, or canonical serializer exists yet. The JSON below is a hand-drafted illustration of the shape README.md describes, not generated or validated code."
    )}
    <h2>Illustrative bundle (mock/rule_schema.json)</h2>
    <pre class="json-view">${pretty(schema)}</pre>
  `;
}
