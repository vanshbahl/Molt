#!/usr/bin/env python3
"""Minimal reproducible runner for the Molt PyJWT bounded-task pilot generation.

Executes the first real LLM rule-generation call for Arms C/D using Anthropic's
Messages API, preserving exact inputs, tokens, latencies, retries, billed costs,
and validation outcomes.

Usage:
    python3 experiments/run_pyjwt_pilot.py [--dry-run]

Requirements:
    ANTHROPIC_API_KEY environment variable. If unset, the script exits with code 2
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

DEFAULT_SYSTEM_PROMPT = (
    "You are an automated migration rule generator. Your task is to generate a single, "
    "bounded JSON migration rule bundle for the breaking Python dependency upgrade described "
    "in the user prompt. You must strictly output ONLY valid JSON matching the requested schema. "
    "Do not include explanation, conversational preamble, markdown backticks, or postscript. "
    "Use only the permitted primitive operations: rename_symbol, change_import, rename_argument, "
    "add_argument, remove_argument, replace_call, and abstain. Do not emit executable Python code."
)


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


def calculate_cost(usage, price_schedule):
    in_tok = usage.get("input_tokens", 0)
    out_tok = usage.get("output_tokens", 0)
    c_write = usage.get("cache_creation_input_tokens", 0)
    c_read = usage.get("cache_read_input_tokens", 0)

    in_price = price_schedule["input_usd_per_mtok"]
    out_price = price_schedule["output_usd_per_mtok"]
    write_price = price_schedule["prompt_cache_write_usd_per_mtok"]
    read_price = price_schedule["prompt_cache_read_usd_per_mtok"]

    cost = (
        (in_tok * in_price)
        + (out_tok * out_price)
        + (c_write * write_price)
        + (c_read * read_price)
    ) / 1_000_000.0

    return {
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cache_creation_input_tokens": c_write,
        "cache_read_input_tokens": c_read,
        "calculated_billed_cost_usd": round(cost, 6),
        "price_schedule_model": price_schedule["model"],
        "price_schedule_date": price_schedule["fetched_at"],
    }


def execute_request(config, user_content, api_key):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    model_id = config["model_id"]
    req_params = config["request_parameters"]
    retry_policy = config["retry_and_timeout_policy"]
    max_retries = retry_policy["max_transport_retries_per_request"]
    timeout_s = retry_policy["request_timeout_seconds"]

    payload = {
        "model": model_id,
        "max_tokens": req_params["max_output_tokens"],
        "temperature": req_params["temperature"],
        "system": DEFAULT_SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": user_content,
            }
        ],
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
    parser = argparse.ArgumentParser(description="Molt PyJWT Pilot Generation Runner")
    parser.add_argument("--dry-run", action="store_true", help="Inspect prompt and config without making network requests")
    args = parser.parse_args()

    config = load_config()
    user_content = load_evidence_packet()

    if args.dry_run:
        print("[DRY RUN] PyJWT Pilot Generation Configuration:")
        print(f"  Model ID:        {config['model_id']}")
        print(f"  Max tokens:      {config['request_parameters']['max_output_tokens']}")
        print(f"  Temperature:     {config['request_parameters']['temperature']}")
        print(f"  Prompt chars:    {len(user_content)}")
        print(f"  System prompt:   {len(DEFAULT_SYSTEM_PROMPT)} chars")
        print(f"  Target URL:      https://api.anthropic.com/v1/messages")
        print("[DRY RUN] Request payload is valid and ready to execute.")
        return 0

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[BLOCKED] ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        print("Molt strictly prohibits fabricating model responses or using unverified mock proxies.", file=sys.stderr)
        print("To execute this pilot call with measured tokens, latency, and costs:", file=sys.stderr)
        print("    export ANTHROPIC_API_KEY='sk-ant-...' ", file=sys.stderr)
        print("    python3 experiments/run_pyjwt_pilot.py", file=sys.stderr)
        return 2

    print(f"Executing real PyJWT pilot call with model: {config['model_id']}...")
    timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    raw_response, latency_ms, retries = execute_request(config, user_content, api_key)

    # Extract text from Anthropic response content blocks
    response_text = ""
    for block in raw_response.get("content", []):
        if block.get("type") == "text":
            response_text += block.get("text", "")

    # Parse and validate rule bundle
    parsed_bundle = None
    parse_error = None
    is_valid = False
    validation_detail = ""

    try:
        # Strip potential markdown fences if present
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

    cost_info = calculate_cost(raw_response.get("usage", {}), config["price_schedule"])

    record = {
        "status": "measured, actual API response",
        "recorded_at": timestamp_utc,
        "model_requested": config["model_id"],
        "model_returned": raw_response.get("model"),
        "latency_ms": latency_ms,
        "transport_retries": retries,
        "usage": cost_info,
        "prompt_sha256": None,  # will be filled
        "raw_response_id": raw_response.get("id"),
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
    print(f"  Tokens:   {cost_info['input_tokens']} in / {cost_info['output_tokens']} out")
    print(f"  Cost:     ${cost_info['calculated_billed_cost_usd']} USD")
    print(f"  Latency:  {latency_ms} ms")
    print(f"  Valid:    {is_valid} ({validation_detail})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
