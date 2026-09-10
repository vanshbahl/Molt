#!/usr/bin/env python3
"""Minimal reproducible runner for the Molt PyJWT bounded-task pilot generation.

Executes the first real LLM rule-generation call for Arms C/D using the
Google Gemini Developer API Free Tier, preserving exact inputs, tokens,
latencies, retries, monetary costs ($0 on Free Tier), and validation outcomes.

Usage:
    python3 experiments/run_pyjwt_pilot.py [--dry-run]

Requirements:
    GEMINI_API_KEY environment variable. If unset, the script exits with code 2
    and reports that execution remains blocked. Never hardcode API keys.
"""

import argparse
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
CONFIG_PATH = EXPERIMENTS_DIR / "pilot_config.json"
PACKET_PATH = EXPERIMENTS_DIR / "pilot_evidence_packet.md"
SCHEMA_PATH = EXPERIMENTS_DIR / "rule_schema.json"
MEASURED_RUNS_DIR = EXPERIMENTS_DIR / "measured_runs"
OUTPUT_PATH = MEASURED_RUNS_DIR / "pilot_pyjwt_result.json"
DOTENV_PATH = REPO_ROOT / ".env"

DEFAULT_SYSTEM_PROMPT = (
    "You are an automated migration rule generator. Your task is to generate a single, "
    "bounded JSON migration rule bundle for the breaking Python dependency upgrade described "
    "in the user prompt. You must strictly output ONLY valid JSON matching the requested schema. "
    "Do not include explanation, conversational preamble, markdown backticks, or postscript. "
    "Use only the permitted primitive operations: rename_symbol, change_import, rename_argument, "
    "add_argument, remove_argument, replace_call, and abstain. Do not emit executable Python code."
)


def load_dotenv(dotenv_path=DOTENV_PATH):
    """Load key-value pairs from a local .env file into os.environ if unset."""
    path = pathlib.Path(dotenv_path)
    if not path.is_file():
        return False
    try:
        import dotenv  # type: ignore
        dotenv.load_dotenv(dotenv_path=path, override=False)
        return True
    except ImportError:
        pass

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        return False

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val
    return True


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_evidence_packet():
    text = PACKET_PATH.read_text(encoding="utf-8")
    parts = text.split("\n---\n")
    if len(parts) >= 3:
        # Standard header / body / bookkeeping split
        return parts[1].strip("\n")
    return text.strip()


def validate_rule_bundle(rule_json):
    """Validate parsed JSON against basic canonical schema requirements."""
    required_envelope = {"bundle_id", "bundle_version", "applies_to", "operations"}
    if not isinstance(rule_json, dict):
        return False, "Response root is not a JSON object"
    missing = required_envelope - set(rule_json.keys())
    if missing:
        return False, f"Missing required envelope keys: {sorted(missing)}"

    applies_to = rule_json.get("applies_to", {})
    if not isinstance(applies_to, dict) or not {"library", "old_version_range", "new_version"}.issubset(applies_to.keys()):
        return False, "applies_to must contain library, old_version_range, and new_version"

    ops = rule_json.get("operations", [])
    if not isinstance(ops, list) or len(ops) == 0:
        return False, "operations must be a non-empty list"

    valid_ops = {"rename_symbol", "change_import", "rename_argument", "add_argument", "remove_argument", "replace_call", "abstain"}
    for idx, op in enumerate(ops):
        if not isinstance(op, dict) or "op" not in op:
            return False, f"Operation #{idx} is not a valid dict with an 'op' field"
        if op["op"] not in valid_ops:
            return False, f"Operation #{idx} uses unauthorized primitive: {op['op']}"

    return True, "Valid Molt rule bundle"


def execute_gemini_request(config, user_content, api_key):
    model_id = config["model_id"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
    headers = {
        "x-goog-api-key": api_key,
        "content-type": "application/json",
    }

    req_params = config["request_parameters"]
    retry_policy = config["retry_and_timeout_policy"]
    max_retries = retry_policy["max_transport_retries_per_request"]
    timeout_s = retry_policy["request_timeout_seconds"]

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": user_content,
                    }
                ],
            }
        ],
        "systemInstruction": {
            "parts": [
                {
                    "text": DEFAULT_SYSTEM_PROMPT,
                }
            ]
        },
        "generationConfig": {
            "temperature": req_params["temperature"],
            "maxOutputTokens": req_params["max_output_tokens"],
            "responseMimeType": req_params.get("response_mime_type", "application/json"),
        },
    }

    body_bytes = json.dumps(payload).encode("utf-8")
    attempts = 0
    last_err = None

    while attempts <= max_retries:
        attempts += 1
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        start_time = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                resp_bytes = resp.read()
                data = json.loads(resp_bytes.decode("utf-8"))
                return data, latency_ms, attempts - 1
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            last_err = e
            if attempts <= max_retries:
                backoff_s = 2 ** attempts
                print(f"[WARN] Request attempt {attempts} failed ({e}). Retrying in {backoff_s}s...", file=sys.stderr)
                time.sleep(backoff_s)
            else:
                raise RuntimeError(f"Request failed after {attempts} attempts: {last_err}") from last_err


def main():
    parser = argparse.ArgumentParser(description="Molt PyJWT Pilot Generation Runner (Gemini Free Tier)")
    parser.add_argument("--dry-run", action="store_true", help="Inspect prompt and config without making network requests")
    args = parser.parse_args()

    load_dotenv()

    config = load_config()
    user_content = load_evidence_packet()

    if args.dry_run:
        print("[DRY RUN] PyJWT Pilot Generation Configuration (Google Gemini Developer API):")
        print(f"  Provider:        {config['provider']}")
        print(f"  Model ID:        {config['model_id']}")
        print(f"  Tier:            {config.get('price_schedule', {}).get('tier', 'Free Tier')}")
        print(f"  Credential Env:  {config.get('credential_env', 'GEMINI_API_KEY')}")
        print(f"  Max tokens:      {config['request_parameters']['max_output_tokens']}")
        print(f"  Temperature:     {config['request_parameters']['temperature']}")
        print(f"  Prompt chars:    {len(user_content)}")
        print(f"  System prompt:   {len(DEFAULT_SYSTEM_PROMPT)} chars")
        print(f"  Target URL:      https://generativelanguage.googleapis.com/v1beta/models/{config['model_id']}:generateContent")
        print(f"  Monetary Cost:   $0.00 (Strict zero-cost constraint)")
        print("[DRY RUN] Request payload and configuration are valid.")
        return 0

    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        print("[BLOCKED] GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Molt operates under a strict zero-monetary-cost constraint using the Google Gemini Developer API Free Tier.", file=sys.stderr)
        print("No paid billing or Anthropic credential is required.", file=sys.stderr)
        print("To execute this pilot call at $0 monetary cost:", file=sys.stderr)
        print("    export GEMINI_API_KEY='your-gemini-api-key' (or add to .env)", file=sys.stderr)
        print("    python3 experiments/run_pyjwt_pilot.py", file=sys.stderr)
        return 2

    print(f"Executing real PyJWT pilot call with model: {config['model_id']} (Google Gemini Developer API Free Tier)...")
    timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw_response, latency_ms, retries = execute_gemini_request(config, user_content, api_key)

    # Extract text from Gemini candidates
    response_text = ""
    candidates = raw_response.get("candidates", [])
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "text" in part:
                response_text += part["text"]

    # Extract usage metadata
    usage = raw_response.get("usageMetadata", {})
    prompt_tokens = usage.get("promptTokenCount", 0)
    completion_tokens = usage.get("candidatesTokenCount", 0)
    thinking_tokens = usage.get("thoughtsTokenCount", 0)
    total_tokens = usage.get("totalTokenCount", prompt_tokens + completion_tokens)

    # Parse and validate rule bundle
    parsed_bundle = None
    parse_error = None
    is_valid = False
    validation_detail = ""

    try:
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        parsed_bundle = json.loads(clean_text)
        is_valid, validation_detail = validate_rule_bundle(parsed_bundle)
    except Exception as e:
        parse_error = str(e)
        validation_detail = f"JSON parse error: {e}"

    record = {
        "status": "measured, actual API response",
        "provider": config["provider"],
        "model_requested": config["model_id"],
        "model_version_returned": raw_response.get("modelVersion", config["model_id"]),
        "tier": "Google Gemini Developer API Free Tier",
        "monetary_cost_usd": 0.0,
        "recorded_at": timestamp_utc,
        "latency_ms": latency_ms,
        "transport_retries": retries,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "thinking_tokens": thinking_tokens,
            "total_tokens": total_tokens,
            "monetary_cost_usd": 0.0,
            "billing_note": "Free Tier access, zero monetary charges incurred."
        },
        "raw_response": raw_response,
        "raw_response_text": response_text,
        "parsed_rule_bundle": parsed_bundle,
        "parse_error": parse_error,
        "schema_valid": is_valid,
        "validation_detail": validation_detail,
    }

    MEASURED_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    print(f"[SUCCESS] Measured pilot call captured to {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    print(f"  Provider: {config['provider']} ({record['tier']})")
    print(f"  Model:    {record['model_version_returned']}")
    print(f"  Tokens:   {prompt_tokens} in / {completion_tokens} out (Total: {total_tokens})")
    print(f"  Cost:     $0.00 USD (Free Tier)")
    print(f"  Latency:  {latency_ms} ms")
    print(f"  Valid:    {is_valid} ({validation_detail})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
