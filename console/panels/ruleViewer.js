import { fetchJson, escapeHtml, calloutMockSection, calloutRealSection, pretty } from "./_util.js";

export async function render(root) {
  const schema = await fetchJson("./mock/rule_schema.json");
  const packetRes = await fetch("../../experiments/pilot_evidence_packet.md");
  const packetMd = packetRes.ok ? await packetRes.text() : "";
  const fenceStart = packetMd.indexOf("```json");
  const codeStart = packetMd.indexOf("\n", fenceStart) + 1;
  const fenceEnd = packetMd.indexOf("```", codeStart);
  const targetShape = fenceStart !== -1 ? packetMd.slice(codeStart, fenceEnd).trim() : null;

  root.innerHTML = `
    <h1>Rule JSON / Schema Viewer</h1>
    <p class="panel-intro">Will eventually render <code>rules/schema.py</code>'s exported JSON Schema and validated rule bundles (Phase 1). For now this is a raw JSON viewer over hand-written illustrations.</p>

    <h2>Pilot's requested output shape</h2>
    ${calloutRealSection(
      "Real instruction content, not yet sent, not the frozen Phase 1 schema",
      "This is the literal output-format block from experiments/pilot_evidence_packet.md — real content that WOULD be sent to the model, not a schema it has validated against or a call it has answered. It is deliberately informal (only the six primitive op names are fixed) because rules/schema.py does not exist."
    )}
    ${targetShape ? `<pre class="json-view">${escapeHtml(targetShape)}</pre>` : `<p class="panel-intro">(could not load pilot_evidence_packet.md)</p>`}

    <h2>Illustrative bundle (mock/rule_schema.json)</h2>
    ${calloutMockSection(
      "Nothing here is a real schema",
      "No rule schema, validator, or canonical serializer exists yet. The JSON below is a hand-drafted illustration of the shape README.md describes, not generated or validated code."
    )}
    <pre class="json-view">${pretty(schema)}</pre>
  `;
}
