"""Pilot runner behaviour with an injected fake transport. No network, ever."""

import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import isolated_env

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "experiments" / "run_pyjwt_pilot.py"

spec = importlib.util.spec_from_file_location("run_pyjwt_pilot", SCRIPT)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

VALID_RULE_TEXT = (REPO_ROOT / "migrations" / "pyjwt-1-to-2" / "rule.json").read_text()


def gemini_response(text, finish="STOP", usage=None):
    return {
        "candidates": [{"content": {"parts": [{"text": text}]}, "finishReason": finish}],
        "usageMetadata": usage if usage is not None else {
            "promptTokenCount": 4000, "candidatesTokenCount": 350, "thoughtsTokenCount": 120, "totalTokenCount": 4470},
        "modelVersion": "gemini-3.7-flash-test",
    }


class FakeTransport:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, body, headers, timeout):
        self.calls.append({"url": url, "payload": json.loads(body), "has_key": bool(headers.get("x-goog-api-key"))})
        status, data = self.responses.pop(0)
        if isinstance(data, Exception):
            raise data
        return status, json.dumps(data).encode()


@pytest.fixture
def live_env(monkeypatch):
    """Simulate an operator environment; the transport is still fake."""
    monkeypatch.delenv("MOLT_NO_NETWORK", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")


def run_main(tmp_path, transport, *args):
    return runner.main(["--confirm-free-tier", *args], transport=transport, sleep=lambda s: None, out_dir=tmp_path)


def only_record(tmp_path):
    files = sorted(tmp_path.glob("pyjwt_pilot_*.json"))
    assert len(files) == 1
    return files[0], json.loads(files[0].read_text())


# ---------------------------------------------------------------------------
# Gates: nothing reaches a transport unless every condition holds
# ---------------------------------------------------------------------------


def test_dry_run_needs_no_key_and_makes_no_request(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(runner, "load_env_file", lambda *_: pytest.fail("dry run must not read env files"))
    transport = FakeTransport()
    assert runner.main(["--dry-run"], transport=transport, out_dir=tmp_path) == 0
    out = capsys.readouterr().out
    assert "gemini-3.7-flash" in out and "reference rule valid=True" in out
    assert transport.calls == [] and list(tmp_path.iterdir()) == []


def test_dry_run_subprocess_with_isolated_env():
    res = subprocess.run([sys.executable, str(SCRIPT), "--dry-run"], capture_output=True, text=True,
                         env=isolated_env(), cwd=REPO_ROOT)
    assert res.returncode == 0, res.stderr
    assert "No network request" in res.stdout


def test_no_key_blocks_and_env_file_is_never_implicit(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("MOLT_NO_NETWORK", raising=False)
    monkeypatch.setattr(runner, "load_env_file", lambda *_: pytest.fail(".env must not be loaded implicitly"))
    transport = FakeTransport()
    assert runner.main(["--confirm-free-tier"], transport=transport, out_dir=tmp_path) == runner.EXIT_BLOCKED
    assert "GEMINI_API_KEY is not set" in capsys.readouterr().err
    assert transport.calls == []


def test_network_disabled_flag_wins_even_with_key(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-test-key")  # MOLT_NO_NETWORK stays set by conftest
    transport = FakeTransport()
    assert run_main(tmp_path, transport) == runner.EXIT_NETWORK_DISABLED
    assert transport.calls == []


def test_live_call_requires_free_tier_confirmation(tmp_path, live_env, capsys):
    transport = FakeTransport()
    assert runner.main([], transport=transport, out_dir=tmp_path) == runner.EXIT_BLOCKED
    assert "--confirm-free-tier" in capsys.readouterr().err
    assert transport.calls == []


def test_explicit_env_file_is_loaded_without_printing(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    env_file = tmp_path / "custom.env"
    env_file.write_text("GEMINI_API_KEY='from-file-123'\n# comment\n", encoding="utf-8")
    assert runner.load_env_file(env_file)
    assert os.environ["GEMINI_API_KEY"] == "from-file-123"
    assert "from-file-123" not in capsys.readouterr().out
    monkeypatch.delenv("GEMINI_API_KEY")


def test_subprocess_without_key_blocks(tmp_path):
    env = isolated_env()
    env.pop("MOLT_NO_NETWORK")
    res = subprocess.run([sys.executable, str(SCRIPT), "--confirm-free-tier"], capture_output=True, text=True,
                         env=env, cwd=REPO_ROOT)
    assert res.returncode == runner.EXIT_BLOCKED and "[BLOCKED]" in res.stderr


# ---------------------------------------------------------------------------
# Execution with a fake transport
# ---------------------------------------------------------------------------


def test_valid_responses_for_each_configured_replicate(tmp_path, live_env):
    transport = FakeTransport((200, gemini_response(VALID_RULE_TEXT)), (200, gemini_response(VALID_RULE_TEXT)))
    assert run_main(tmp_path, transport) == 0
    assert len(transport.calls) == runner.load_config()["generation_replicates_pyjwt_pilot"] == 2
    payload = transport.calls[0]["payload"]
    assert payload["generationConfig"]["thinkingConfig"] == {"thinkingLevel": "low"}
    assert payload["generationConfig"]["maxOutputTokens"] == 8192
    assert '"schema_version": { "const": "molt.rule.v2" }' in payload["contents"][0]["parts"][0]["text"]
    path, rec = only_record(tmp_path)
    assert rec["status"].startswith("measured")
    assert rec["summary"] == {"replicates_completed": 2, "valid_proposals": 2, "total_requests_sent": 2}
    r1 = rec["replicates"][0]
    assert r1["replicate"] == 1 and r1["started_at"] and r1["latency_ms"] is not None
    assert r1["usage"]["output_tokens"] == 350 and r1["usage"]["thinking_tokens"] == 120
    assert r1["usage"]["cached_prompt_tokens"] is None  # missing usage is unavailable, never 0
    assert r1["validation"]["valid"] and r1["model_version_returned"] == "gemini-3.7-flash-test"
    assert r1["cost"]["basis"] == "operator_assertion"
    assert "fake-test-key" not in path.read_text()


def test_permanent_4xx_is_not_retried_and_stops_the_run(tmp_path, live_env):
    transport = FakeTransport((404, {"error": {"status": "NOT_FOUND", "message": "model not found"}}))
    assert run_main(tmp_path, transport) == runner.EXIT_ERROR
    assert len(transport.calls) == 1
    _, rec = only_record(tmp_path)
    r = rec["replicates"][0]
    assert r["request_status"] == "permanent_error" and "NOT_FOUND" in r["error"]
    assert rec["stopped_early"] and len(rec["replicates"]) == 1


@pytest.mark.parametrize("code", [400, 401, 403])
def test_other_permanent_codes_not_retried(tmp_path, live_env, code):
    transport = FakeTransport((code, {"error": {"status": "X", "message": "bad"}}))
    run_main(tmp_path, transport, "--replicates", "1")
    assert len(transport.calls) == 1


def test_transient_errors_are_retried_within_cap(tmp_path, live_env):
    transport = FakeTransport((503, {"error": {"message": "overloaded"}}), (429, {"error": {"message": "rate"}}),
                              (200, gemini_response(VALID_RULE_TEXT)))
    assert run_main(tmp_path, transport, "--replicates", "1") == 0
    _, rec = only_record(tmp_path)
    assert [a["http_status"] for a in rec["replicates"][0]["attempts"]] == [503, 429, 200]


def test_transport_failure_after_cap_is_recorded(tmp_path, live_env):
    transport = FakeTransport(*[(None, OSError("connection reset"))] * 3)
    assert run_main(tmp_path, transport, "--replicates", "1") == runner.EXIT_ERROR
    _, rec = only_record(tmp_path)
    assert rec["replicates"][0]["request_status"] == "transport_failure"
    assert len(transport.calls) == 3  # 1 + max_transport_retries_per_request (2)


def test_truncated_output_is_an_invalid_proposal(tmp_path, live_env):
    transport = FakeTransport((200, gemini_response('{"schema_version": "molt.rule.v2", "bundle_id": "py', finish="MAX_TOKENS")))
    run_main(tmp_path, transport, "--replicates", "1")
    _, rec = only_record(tmp_path)
    r = rec["replicates"][0]
    assert r["truncated"] and not r["validation"]["valid"] and "MAX_TOKENS" in r["validation"]["truncation_note"]


def test_schema_invalid_output_is_rejected_with_reasons(tmp_path, live_env):
    bad = json.loads(VALID_RULE_TEXT)
    bad["operations"].append({"op": "add_argument", "id": "x", "target_call": "jwt.decode", "arg_name": "leeway",
                              "default_value": "__import__('os')"})
    transport = FakeTransport((200, gemini_response("```json\n" + json.dumps(bad) + "\n```")))
    run_main(tmp_path, transport, "--replicates", "1")
    _, rec = only_record(tmp_path)
    v = rec["replicates"][0]["validation"]
    assert v["json_parsed"] and not v["schema_valid"] and v["schema_errors"]


def test_semantically_invalid_output_is_rejected(tmp_path, live_env):
    bad = json.loads(VALID_RULE_TEXT)
    bad["operations"][1]["id"] = bad["operations"][0]["id"]
    transport = FakeTransport((200, gemini_response(json.dumps(bad))))
    run_main(tmp_path, transport, "--replicates", "1")
    v = only_record(tmp_path)[1]["replicates"][0]["validation"]
    assert v["schema_valid"] and not v["semantic_valid"] and "duplicate" in v["semantic_errors"][0]


def test_non_json_output_is_recorded(tmp_path, live_env):
    run_main(tmp_path, FakeTransport((200, gemini_response("Sure! Here is the rule..."))), "--replicates", "1")
    v = only_record(tmp_path)[1]["replicates"][0]["validation"]
    assert not v["json_parsed"] and v["parse_error"]


def test_each_run_writes_a_new_read_only_file(tmp_path, live_env):
    for _ in range(2):
        run_main(tmp_path, FakeTransport((200, gemini_response(VALID_RULE_TEXT))), "--replicates", "1")
    files = sorted(tmp_path.glob("pyjwt_pilot_*.json"))
    assert len(files) == 2 and files[0].name != files[1].name
    for f in files:
        assert not (f.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    record = json.loads(files[0].read_text())
    with pytest.raises(FileExistsError):
        runner.write_immutable(record, tmp_path)


def test_cost_unknown_without_operator_assertion(tmp_path, live_env):
    config = runner.load_config()
    rec, _ = runner.run_pilot(config, "fake-test-key", 1, transport=FakeTransport((200, gemini_response(VALID_RULE_TEXT))),
                              sleep=lambda s: None, out_dir=tmp_path, free_tier_confirmed=False)
    assert rec["replicates"][0]["cost"] == {"monetary_cost_usd": None, "basis": "unknown",
                                            "note": "Billing tier of the key's project is not observable."}


def test_replicate_override_is_bounded(tmp_path, live_env):
    assert run_main(tmp_path, FakeTransport(), "--replicates", "3") == runner.EXIT_ERROR


def test_packet_and_schema_are_both_sent():
    content = runner.build_user_content()
    assert "## Frozen development exemplar" in content and "molt.rule.v2" in content
    assert "Packet ends above this line" not in content
