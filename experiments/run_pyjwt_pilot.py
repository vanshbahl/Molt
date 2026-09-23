#!/usr/bin/env python3
"""PyJWT bounded-task rule-generation pilot (initial proposals only).

Sends the frozen evidence packet plus the canonical rule schema to the pinned
Gemini model once per configured replicate, validates every response against
experiments/rule_schema.json (jsonschema) and Molt's semantic rules, and
writes ONE immutable result file per run under experiments/measured_runs/.

This runner makes network calls only when ALL of these hold:
  * --dry-run is not given;
  * GEMINI_API_KEY is set (in the environment, or via an explicit --env-file);
  * --confirm-free-tier is given, i.e. the operator asserts that the key's
    Google Cloud project has no billing account linked (Free Tier). Billing
    status cannot be observed through the API, so the runner will not assume it;
  * MOLT_NO_NETWORK is not set (the test suite sets it).

Monetary cost is recorded as unknown (null) unless the operator confirmed the
Free Tier, in which case it is recorded as the operator-asserted expected
charge of $0.00, labelled as an assertion rather than a billing measurement.

The repair sweep (1/2/3/5 proposals) is NOT executed here; that is M5.

Usage:
    python3 experiments/run_pyjwt_pilot.py --dry-run
    python3 experiments/run_pyjwt_pilot.py --env-file .env --confirm-free-tier
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import secrets
import sys
import time
import urllib.error
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
CONFIG_PATH = EXPERIMENTS_DIR / "pilot_config.json"
PACKET_PATH = EXPERIMENTS_DIR / "pilot_evidence_packet.md"
SCHEMA_PATH = EXPERIMENTS_DIR / "rule_schema.json"
REFERENCE_RULE_PATH = REPO_ROOT / "migrations" / "pyjwt-1-to-2" / "rule.json"
MEASURED_RUNS_DIR = EXPERIMENTS_DIR / "measured_runs"
API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"

EXIT_OK, EXIT_ERROR, EXIT_BLOCKED, EXIT_NETWORK_DISABLED = 0, 1, 2, 3
PERMANENT_HTTP = {400, 401, 403, 404, 405, 409, 413, 422}
TRANSIENT_HTTP = {429, 500, 502, 503, 504}

DEFAULT_SYSTEM_PROMPT = (
    "You are an automated migration rule generator. Your task is to generate a single, "
    "bounded JSON migration rule bundle for the breaking Python dependency upgrade described "
    "in the user prompt. You must strictly output ONLY valid JSON matching the requested schema. "
    "Do not include explanation, conversational preamble, markdown backticks, or postscript. "
    "Use only the permitted primitive operations: rename_symbol, change_import, rename_argument, "
    "add_argument, remove_argument, replace_call, and abstain. Do not emit executable Python code."
)

sys.path.insert(0, str(REPO_ROOT / "src"))


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def load_env_file(path) -> bool:
    """Load KEY=VALUE lines from an explicitly named dotenv file (never implicit).

    Existing environment variables win. Values are never printed.
    """
    path = pathlib.Path(path)
    if not path.is_file():
        return False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = (s.strip() for s in line.split("=", 1))
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val
    return True


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_evidence_packet() -> str:
    parts = PACKET_PATH.read_text(encoding="utf-8").split("\n---\n")
    if len(parts) != 3:
        raise ValueError("evidence packet must have exactly header / body / bookkeeping sections")
    return parts[1].strip("\n")


def build_user_content() -> str:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8").strip()
    return f"{load_evidence_packet()}\n\n## Rule schema (JSON Schema, molt.rule.v2)\n\n```json\n{schema_text}\n```\n"


def build_payload(config: dict, user_content: str) -> dict:
    params = config["request_parameters"]
    generation = {
        "temperature": params["temperature"],
        "maxOutputTokens": params["max_output_tokens"],
        "responseMimeType": params.get("response_mime_type", "application/json"),
    }
    if params.get("thinking_config"):
        generation["thinkingConfig"] = params["thinking_config"]
    return {
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "systemInstruction": {"parts": [{"text": DEFAULT_SYSTEM_PROMPT}]},
        "generationConfig": generation,
    }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def strip_fences(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def validate_response_text(text: str) -> dict:
    """Parse and validate a model response. Never raises."""
    out = {"json_parsed": False, "parse_error": None, "schema_valid": False, "schema_errors": [],
           "semantic_valid": False, "semantic_errors": [], "valid": False, "parsed_rule_bundle": None}
    try:
        data = json.loads(strip_fences(text))
    except (json.JSONDecodeError, ValueError) as exc:
        out["parse_error"] = str(exc)
        return out
    out["json_parsed"] = True
    out["parsed_rule_bundle"] = data

    from jsonschema import Draft202012Validator

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.absolute_path))
    out["schema_errors"] = [f"$/{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors]
    out["schema_valid"] = not errors
    if out["schema_valid"]:
        from molt.schema import semantic_errors

        out["semantic_errors"] = [str(i) for i in semantic_errors(data)]
        out["semantic_valid"] = not out["semantic_errors"]
    out["valid"] = out["schema_valid"] and out["semantic_valid"]
    return out


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------


class RequestFailed(Exception):
    def __init__(self, message, attempts, permanent):
        super().__init__(message)
        self.attempts = attempts
        self.permanent = permanent


def urllib_transport(url: str, body: bytes, headers: dict, timeout: float):
    """Return (status_code, response_bytes). Raises OSError on transport failure."""
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _error_summary(body: bytes) -> str:
    try:
        err = json.loads(body.decode("utf-8")).get("error", {})
        return f"{err.get('status', '')} {err.get('message', '')}".strip()[:500]
    except (ValueError, AttributeError):
        return body[:200].decode("utf-8", "replace")


def send_request(config: dict, payload: dict, api_key: str, transport=urllib_transport, sleep=time.sleep):
    """POST with bounded retries. Permanent 4xx errors are never retried.

    Returns (response_json, latency_ms, attempts) where attempts lists every try.
    """
    policy = config["retry_and_timeout_policy"]
    max_retries = policy["max_transport_retries_per_request"]
    url = f"{API_ROOT}/{config['model_id']}:generateContent"
    headers = {"x-goog-api-key": api_key, "content-type": "application/json"}
    body = json.dumps(payload).encode("utf-8")
    attempts = []
    for attempt in range(max_retries + 1):
        start = time.perf_counter()
        try:
            status, data = transport(url, body, headers, policy["request_timeout_seconds"])
        except OSError as exc:  # URLError, timeouts, connection resets
            status, data, detail = None, b"", f"transport error: {exc}"
        else:
            detail = None if status == 200 else _error_summary(data)
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        attempts.append({"attempt": attempt + 1, "http_status": status, "latency_ms": latency_ms, "error": detail})
        if status == 200:
            return json.loads(data.decode("utf-8")), latency_ms, attempts
        if status in PERMANENT_HTTP or (status is not None and status not in TRANSIENT_HTTP and 400 <= status < 500):
            raise RequestFailed(f"HTTP {status} (permanent, not retried): {detail}", attempts, permanent=True)
        if attempt < max_retries:
            sleep(2 ** (attempt + 1))
    raise RequestFailed(f"gave up after {len(attempts)} attempts: {attempts[-1]['error']}", attempts, permanent=False)


# ---------------------------------------------------------------------------
# Result extraction
# ---------------------------------------------------------------------------


def extract(response: dict) -> dict:
    candidates = response.get("candidates") or []
    first = candidates[0] if candidates else {}
    parts = (first.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
    usage = response.get("usageMetadata") or {}
    finish = first.get("finishReason")

    def tok(key):
        return usage.get(key)  # missing usage stays None ("unavailable"), never 0

    return {
        "text": text,
        "finish_reason": finish,
        "truncated": finish == "MAX_TOKENS",
        "blocked": bool((response.get("promptFeedback") or {}).get("blockReason")) or finish in {"SAFETY", "RECITATION", "PROHIBITED_CONTENT"},
        "model_version_returned": response.get("modelVersion"),
        "response_id": response.get("responseId"),
        "usage": {
            "prompt_tokens": tok("promptTokenCount"),
            "cached_prompt_tokens": tok("cachedContentTokenCount"),
            "output_tokens": tok("candidatesTokenCount"),
            "thinking_tokens": tok("thoughtsTokenCount") if "thoughtsTokenCount" in usage else tok("totalThoughtTokens"),
            "total_tokens": tok("totalTokenCount"),
            "raw_usage_metadata": usage,
        },
    }


def cost_record(free_tier_confirmed: bool) -> dict:
    if free_tier_confirmed:
        return {
            "monetary_cost_usd": 0.0,
            "basis": "operator_assertion",
            "note": "Operator passed --confirm-free-tier asserting the key's project has no billing account; the "
                    "Gemini API does not report billing, so this is an expected $0.00, not a billing measurement.",
        }
    return {"monetary_cost_usd": None, "basis": "unknown", "note": "Billing tier of the key's project is not observable."}


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


def new_run_id(now: datetime.datetime) -> str:
    return now.strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)


def write_immutable(record: dict, out_dir: pathlib.Path) -> pathlib.Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"pyjwt_pilot_{record['run_id']}.json"
    with open(path, "x", encoding="utf-8") as f:  # "x": never overwrite an existing run
        json.dump(record, f, indent=2)
        f.write("\n")
    os.chmod(path, 0o444)
    return path


def run_replicate(index, config, payload, api_key, transport, sleep, free_tier_confirmed) -> dict:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rec = {"replicate": index, "started_at": started, "request_status": None, "attempts": [], "latency_ms": None,
           "cost": cost_record(free_tier_confirmed)}
    try:
        response, latency_ms, attempts = send_request(config, payload, api_key, transport, sleep)
    except RequestFailed as exc:
        rec.update(request_status="permanent_error" if exc.permanent else "transport_failure",
                   error=str(exc), attempts=exc.attempts, validation=None)
        return rec
    info = extract(response)
    validation = validate_response_text(info["text"])
    if info["truncated"]:
        validation["valid"] = False
        validation["truncation_note"] = "finishReason=MAX_TOKENS: output truncated (thinking may have consumed the budget)"
    rec.update(request_status="ok", attempts=attempts, latency_ms=latency_ms, **{k: info[k] for k in (
        "finish_reason", "truncated", "blocked", "model_version_returned", "response_id", "usage")},
               response_text=info["text"], raw_response=response, validation=validation)
    return rec


def run_pilot(config, api_key, replicates, *, transport=urllib_transport, sleep=time.sleep,
              out_dir=MEASURED_RUNS_DIR, free_tier_confirmed=False) -> tuple:
    now = datetime.datetime.now(datetime.timezone.utc)
    user_content = build_user_content()
    payload = build_payload(config, user_content)
    record = {
        "status": "measured, actual API responses",
        "run_id": new_run_id(now),
        "started_at": now.isoformat(),
        "provider": config["provider"],
        "model_requested": config["model_id"],
        "scope": "initial proposals only (Arm C); repair sweep not executed (M5)",
        "replicates_requested": replicates,
        "request_parameters": payload["generationConfig"],
        "prompt": {"system_prompt_sha256": sha256_text(DEFAULT_SYSTEM_PROMPT),
                   "user_content_sha256": sha256_text(user_content), "user_content_chars": len(user_content),
                   "evidence_packet": "experiments/pilot_evidence_packet.md",
                   "schema_sha256": sha256_text(SCHEMA_PATH.read_text(encoding="utf-8"))},
        "free_tier_confirmed_by_operator": free_tier_confirmed,
        "replicates": [],
    }
    min_gap = 60.0 / max(1, config.get("price_schedule", {}).get("quotas", {}).get("requests_per_minute") or 1)
    try:
        for i in range(1, replicates + 1):
            if i > 1:
                sleep(min_gap)
            rec = run_replicate(i, config, payload, api_key, transport, sleep, free_tier_confirmed)
            record["replicates"].append(rec)
            if rec["request_status"] == "permanent_error":
                record["stopped_early"] = "permanent API error; remaining replicates not attempted"
                break
    finally:
        record["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        done = record["replicates"]
        record["summary"] = {
            "replicates_completed": sum(1 for r in done if r["request_status"] == "ok"),
            "valid_proposals": sum(1 for r in done if (r.get("validation") or {}).get("valid")),
            "total_requests_sent": sum(len(r["attempts"]) for r in done),
        }
        path = write_immutable(record, out_dir)
    return record, path


def print_dry_run(config, replicates) -> None:
    user_content = build_user_content()
    payload = build_payload(config, user_content)
    reference = validate_response_text(REFERENCE_RULE_PATH.read_text(encoding="utf-8"))
    print("[DRY RUN] No network request is made and no API key is read.")
    print(f"  Provider:            {config['provider']}")
    print(f"  Model ID:            {config['model_id']}")
    print(f"  Endpoint:            {API_ROOT}/{config['model_id']}:generateContent")
    print(f"  Replicates:          {replicates} (initial proposals only; repair sweep is M5)")
    print(f"  generationConfig:    {json.dumps(payload['generationConfig'], sort_keys=True)}")
    print(f"  User content:        {len(user_content)} chars, sha256 {sha256_text(user_content)[:16]}…")
    print(f"  System prompt:       {len(DEFAULT_SYSTEM_PROMPT)} chars")
    print(f"  Validator self-check: reference rule valid={reference['valid']}")
    print("  Monetary cost:       not knowable from the API; live runs require --confirm-free-tier")
    if not reference["valid"]:
        raise SystemExit(EXIT_ERROR)


def main(argv=None, *, transport=urllib_transport, sleep=time.sleep, out_dir=MEASURED_RUNS_DIR) -> int:
    parser = argparse.ArgumentParser(description="Molt PyJWT pilot generation runner (Gemini).")
    parser.add_argument("--dry-run", action="store_true", help="build and self-check the request; no network, no key")
    parser.add_argument("--env-file", help="explicitly load GEMINI_API_KEY from this dotenv file (never implicit)")
    parser.add_argument("--replicates", type=int, help="override the configured replicate count (1..configured)")
    parser.add_argument("--confirm-free-tier", action="store_true",
                        help="assert the key's Google Cloud project has NO billing account (required for live calls)")
    args = parser.parse_args(argv)

    config = load_config()
    configured = config["generation_replicates_pyjwt_pilot"]
    replicates = args.replicates or configured
    if not 1 <= replicates <= configured:
        print(f"--replicates must be between 1 and the configured {configured}", file=sys.stderr)
        return EXIT_ERROR

    if args.dry_run:
        print_dry_run(config, replicates)
        return EXIT_OK

    if os.environ.get("MOLT_NO_NETWORK"):
        print("[BLOCKED] MOLT_NO_NETWORK is set; refusing to contact the model API.", file=sys.stderr)
        return EXIT_NETWORK_DISABLED
    if args.env_file:
        load_env_file(args.env_file)
    api_key = (os.environ.get(config.get("credential_env", "GEMINI_API_KEY")) or "").strip()
    if not api_key:
        print("[BLOCKED] GEMINI_API_KEY is not set (pass --env-file .env or export it).", file=sys.stderr)
        return EXIT_BLOCKED
    if not args.confirm_free_tier:
        print("[BLOCKED] Refusing a live call without --confirm-free-tier.", file=sys.stderr)
        print("  The API cannot report whether this key's project has billing enabled. Check Google AI Studio", file=sys.stderr)
        print("  (API keys page: the project's plan must show 'Free'), then re-run with --confirm-free-tier.", file=sys.stderr)
        return EXIT_BLOCKED

    record, path = run_pilot(config, api_key, replicates, transport=transport, sleep=sleep,
                             out_dir=out_dir, free_tier_confirmed=True)
    s = record["summary"]
    print(f"Run {record['run_id']} -> {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}")
    for r in record["replicates"]:
        v = r.get("validation") or {}
        print(f"  replicate {r['replicate']}: {r['request_status']}, latency {r['latency_ms']} ms, "
              f"usage {json.dumps({k: v2 for k, v2 in (r.get('usage') or {}).items() if k != 'raw_usage_metadata'})}, "
              f"valid={v.get('valid')}")
    print(f"  completed {s['replicates_completed']}/{replicates}, valid {s['valid_proposals']}, requests {s['total_requests_sent']}")
    return EXIT_OK if s["replicates_completed"] == replicates else EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
