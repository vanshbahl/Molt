"""Consistency checks for the M0 research artifacts.

These are artifact-agreement tests (JSON well-formed, documents agree with each
other and with executable behaviour, protocol hash current). Behavioural tests
live in test_rule_schema.py, test_engine.py, test_pilot_runner.py, etc.

    .venv/bin/python -m pytest -q
"""

import hashlib
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = REPO_ROOT / "experiments"
CONSOLE = REPO_ROOT / "console"
DOCS = REPO_ROOT / "DOCS"


def load_json(relpath):
    return json.loads((REPO_ROOT / relpath).read_text(encoding="utf-8"))


class TestExperimentJsonWellFormed(unittest.TestCase):
    """Every experiments/*.json file must at least parse and be a dict."""

    def test_all_experiment_json_files_parse(self):
        json_files = sorted(EXPERIMENTS.glob("*.json"))
        self.assertGreaterEqual(
            len(json_files),
            6,
            "expected candidates/probes/pilot_config/pilot_estimate/ceilings/rule_schema at minimum",
        )
        for path in json_files:
            with self.subTest(file=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)


class TestCandidatesConsistency(unittest.TestCase):
    def setUp(self):
        self.data = load_json("experiments/candidates.json")

    def test_pilot_recommendation_ids_exist_in_candidates(self):
        ids = {c["id"] for c in self.data["candidates"]}
        for pilot_id in self.data["pilot_recommendation"]:
            self.assertIn(pilot_id, ids)

    def test_pyjwt_is_a_pilot_candidate(self):
        self.assertIn("pyjwt-1-to-2", self.data["pilot_recommendation"])

    def test_every_candidate_has_required_fields(self):
        required = {"id", "library", "role", "tier_mix", "reproducibility", "sources"}
        for c in self.data["candidates"]:
            with self.subTest(candidate=c.get("id")):
                self.assertTrue(required.issubset(c.keys()), f"missing: {required - c.keys()}")


class TestFeasibilityProbesConsistency(unittest.TestCase):
    def setUp(self):
        self.data = load_json("experiments/feasibility_probes.json")

    def test_bounded_task_probe_present(self):
        ids = {p["candidate_id"] for p in self.data["probes"]}
        self.assertIn(
            "pyjwt-1-to-2-bounded-task",
            ids,
            "the exemplar's grounding probe (exact bounded-task sites) must be recorded",
        )

    def test_every_probe_has_old_pass_and_new_fail_or_mixed(self):
        for p in self.data["probes"]:
            with self.subTest(candidate=p["candidate_id"]):
                self.assertEqual(p["old_result"]["status"], "pass")
                self.assertIn(p["new_result"]["status"], {"fail", "mixed"})

    def test_bounded_task_probe_covers_both_pilot_sites(self):
        probe = next(p for p in self.data["probes"] if p["candidate_id"] == "pyjwt-1-to-2-bounded-task")
        detail = probe["new_result"]["detail"]
        self.assertIn("ExpiredSignature", detail)
        self.assertIn("verify_expiration", detail)


class TestPilotConfigConsistency(unittest.TestCase):
    def setUp(self):
        self.config = load_json("experiments/pilot_config.json")

    def test_provider_is_google(self):
        self.assertIn("Google", self.config["provider"])
        self.assertEqual(self.config["credential_env"], "GEMINI_API_KEY")

    def test_model_is_exact_pinned_gemini_flash(self):
        self.assertEqual(self.config["model_id"], "gemini-3.7-flash")

    def test_repair_sweep_matches_registered_roadmap_values(self):
        self.assertEqual(self.config["repair_proposal_sweep"], [1, 2, 3, 5])

    def test_generation_replicates_is_positive(self):
        self.assertGreaterEqual(self.config["generation_replicates_pyjwt_pilot"], 2)

    def test_thinking_tokens_cannot_starve_output(self):
        params = self.config["request_parameters"]
        self.assertGreaterEqual(params["max_output_tokens"], 4096)
        self.assertIn("thinkingLevel", params["thinking_config"])

    def test_cost_is_not_claimed_as_measured(self):
        p = self.config["price_schedule"]
        self.assertNotIn("effective_monetary_cost_usd", p)
        self.assertIn("billing", p["note"])

    def test_status_is_not_silently_marked_executed(self):
        self.assertIn("not yet executed", self.config["status"])


class TestPilotEstimateConsistency(unittest.TestCase):
    def setUp(self):
        self.estimate = load_json("experiments/pilot_estimate.json")
        self.config = load_json("experiments/pilot_config.json")

    def test_status_is_projection_not_measurement(self):
        self.assertEqual(self.estimate["status"], "projection, not measurement")

    def test_estimate_distinct_from_measurements(self):
        self.assertEqual(self.estimate["status"], "projection, not measurement")
        measured_dir = EXPERIMENTS / "measured_runs"
        if measured_dir.exists():
            for f in measured_dir.glob("*.json"):
                data = json.loads(f.read_text(encoding="utf-8"))
                self.assertIn("status", data)
                self.assertTrue(data["status"].startswith("measured"))

    def test_measured_inputs_are_positive_integers(self):
        m = self.estimate["measured_inputs"]
        for key in ("evidence_packet_chars", "evidence_packet_words", "user_content_chars", "system_prompt_chars"):
            self.assertIsInstance(m[key], int)
            self.assertGreater(m[key], 0)

    def test_measured_counts_match_the_real_request_content(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("run_pyjwt_pilot", EXPERIMENTS / "run_pyjwt_pilot.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        m = self.estimate["measured_inputs"]
        self.assertEqual(len(runner.load_evidence_packet()), m["evidence_packet_chars"], "recompute pilot_estimate.json")
        self.assertEqual(len(runner.build_user_content()), m["user_content_chars"], "recompute pilot_estimate.json")
        self.assertEqual(len(runner.DEFAULT_SYSTEM_PROMPT), m["system_prompt_chars"])

    def test_historical_anthropic_projections_preserved_as_superseded(self):
        hist = self.estimate["superseded_historical_anthropic_projection_usd"]
        self.assertIn("superseded", hist["status"])
        self.assertEqual(hist["model"], "Claude Haiku 4.5")

    def test_monetary_cost_is_conditional_not_asserted(self):
        cost = self.estimate["monetary_cost"]
        self.assertEqual(cost["expected_usd_if_key_project_has_no_billing"], 0.0)
        self.assertIn("not an observable", cost["interpretation"])


class TestCeilingsConsistency(unittest.TestCase):
    def setUp(self):
        self.ceilings = load_json("experiments/ceilings.json")

    def test_spend_ceiling_is_strictly_zero(self):
        self.assertEqual(self.ceilings["spend_ceilings"]["pyjwt_pilot_hard_spend_ceiling_usd"], 0.0)
        self.assertEqual(self.ceilings["spend_ceilings"]["all_project_model_usage_hard_ceiling_usd"], 0.0)

    def test_repair_cap_is_provisional_not_claimed_empirical(self):
        ac = self.ceilings["attempt_ceilings"]
        self.assertNotIn("v1_repair_cap_final_selection", ac)
        self.assertEqual(ac["v1_repair_cap_provisional_default"], 3)
        self.assertIn(ac["v1_repair_cap_provisional_default"], ac["repair_proposal_sweep"])
        self.assertIn("NOT EMPIRICALLY SELECTED", ac["v1_repair_cap_status"])
        self.assertIn("withdrawn", ac["withdrawn_rationale"])

    def test_every_numeric_policy_block_is_labelled(self):
        for key in ("spend_ceilings", "screening_ceilings", "admission_and_expansion", "split_policy", "audit_sampling",
                    "free_tier_quota_ceilings", "retry_ceilings"):
            label = self.ceilings[key]["label"]
            self.assertTrue(any(tag in label for tag in ("EMPIRICAL", "POLICY", "PROVISIONAL")), key)

    def test_expansion_order_uses_known_candidates(self):
        ids = {c["id"] for c in load_json("experiments/candidates.json")["candidates"]}
        self.assertTrue(set(self.ceilings["admission_and_expansion"]["expansion_order"]) <= ids)

    def test_split_and_audit_seeds_match_protocol(self):
        text = (EXPERIMENTS / "protocol.md").read_text(encoding="utf-8")
        for key in ("split_policy", "audit_sampling"):
            self.assertIn(str(self.ceilings[key]["seed"]), text)


class TestRuleLanguageDocumentsAgree(unittest.TestCase):
    """RULE_SPEC, the JSON Schema and the evidence packet must describe the same language."""

    def setUp(self):
        self.schema = load_json("experiments/rule_schema.json")
        self.ops = self.schema["$defs"]["operation"]["properties"]["op"]["enum"]
        self.edit_kinds = [b["properties"]["kind"]["const"] for b in self.schema["$defs"]["argument_edit"]["oneOf"]]
        self.value_types = [b["properties"]["type"]["const"] for b in self.schema["$defs"]["typed_value"]["oneOf"]]

    def test_rule_spec_documents_every_schema_primitive(self):
        doc = (DOCS / "RULE_SPEC.md").read_text(encoding="utf-8")
        self.assertIn(self.schema["properties"]["schema_version"]["const"], doc)
        for name in self.ops + self.edit_kinds:
            self.assertIn(f"`{name}`", doc)
        for name in self.value_types:
            self.assertIn(f'"type": "{name}"', doc)

    def test_evidence_packet_targets_the_same_schema(self):
        packet = (EXPERIMENTS / "pilot_evidence_packet.md").read_text(encoding="utf-8")
        self.assertIn('"schema_version": "molt.rule.v2"', packet)
        for name in self.ops + self.edit_kinds:
            self.assertIn(f"`{name}`", packet)
        self.assertNotIn("default_value", packet)

    def test_runner_system_prompt_lists_every_op(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("run_pyjwt_pilot", EXPERIMENTS / "run_pyjwt_pilot.py")
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        for name in self.ops:
            self.assertIn(name, runner.DEFAULT_SYSTEM_PROMPT)

    def test_schema_has_no_raw_code_fields(self):
        text = json.dumps(self.schema)
        self.assertNotIn("default_value", text)
        self.assertNotIn("captures", text)


class TestConsolePanelsReferenceExistingFiles(unittest.TestCase):
    FETCH_RE = re.compile(r"""fetch(?:Json)?\(\s*["']([^"']+)["']""")

    def test_every_fetched_path_is_served(self):
        """Panels may only fetch console-local files or /data allowlist entries."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("console_serve", CONSOLE / "serve.py")
        serve = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(serve)
        missing = []
        for js_file in sorted((CONSOLE / "panels").glob("*.js")):
            content = js_file.read_text(encoding="utf-8")
            for path in self.FETCH_RE.findall(content):
                self.assertFalse(path.startswith("../"), f"{js_file.name} reaches outside console/: {path}")
                url = "/" + path[2:] if path.startswith("./") else "/" + path
                if serve.resolve_request(url) is None:
                    missing.append(f"{js_file.name} -> {path}")
        self.assertEqual(missing, [], f"panels reference unserved files: {missing}")


class TestProtocolDocConsistency(unittest.TestCase):
    def setUp(self):
        self.text = (EXPERIMENTS / "protocol.md").read_text(encoding="utf-8")

    def test_protocol_version_bumped_and_dated(self):
        self.assertIn("Version 0.5.0 — dated 2026-09-24", self.text)
        self.assertIn("**0.5.0 (2026-09-24):**", self.text)

    def test_protocol_names_the_chosen_model(self):
        self.assertIn(load_json("experiments/pilot_config.json")["model_id"], self.text)

    def test_protocol_does_not_claim_empirical_repair_cap(self):
        self.assertIn("PROVISIONAL default, not an empirically selected value", self.text)
        self.assertNotIn("Frozen V1 Repair Cap", self.text)

    def test_protocol_does_not_claim_m0_closed(self):
        self.assertIn("**M0 is not closed**", self.text)
        self.assertIn("BLOCKED", self.text)

    def test_protocol_cryptographic_hash_matches(self):
        computed = hashlib.sha256((EXPERIMENTS / "protocol.md").read_bytes()).hexdigest()
        recorded = (EXPERIMENTS / "protocol.hash").read_text(encoding="utf-8").split()[0]
        self.assertEqual(computed, recorded, "protocol.md changed: bump version, log the amendment, recompute protocol.hash")


class TestNoStaleStatusClaims(unittest.TestCase):
    """Executable reality wins: status documents must not repeat superseded claims."""

    STALE = [
        "blocked strictly on `GEMINI_API_KEY`",
        "begin Phase 1 / M1 engine development",
        "V1 repair cap frozen at 3",
        "frozen at 3 proposals",
        "priced pilot",
        "billable API key",
        "There is still no engine",
    ]

    def test_status_documents_are_current(self):
        for rel in ("README.md", "DOCS/ROADMAP.md", "DOCS/RULE_SPEC.md", "experiments/protocol.md",
                    "experiments/pilot_evidence_packet.md", "console/README.md"):
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            for phrase in self.STALE:
                with self.subTest(file=rel, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_measured_runs_are_labelled_measured(self):
        for f in (EXPERIMENTS / "measured_runs").glob("*.json"):
            self.assertTrue(json.loads(f.read_text(encoding="utf-8"))["status"].startswith("measured"))


if __name__ == "__main__":
    unittest.main()
