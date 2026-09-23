"""Minimal CLI: ``molt validate RULE`` and ``molt apply RULE REPO``.

``apply`` is a dry run by default: it transforms and verifies a temporary
copy and never touches REPO. ``--write`` publishes the change to REPO only
when the result is PASS.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path

from .engine import apply_rule
from .models import ABSTAIN, FAIL, PASS, UNVERIFIED
from .schema import RuleValidationError, load_rule
from .verifier import resolve_command

EXIT_CODES = {PASS: 0, FAIL: 1, ABSTAIN: 3, UNVERIFIED: 4}


def _cmd_validate(args) -> int:
    try:
        rule = load_rule(args.rule)
    except RuleValidationError as exc:
        print("INVALID")
        for issue in exc.issues:
            print(f"  {issue}")
        return 1
    print(f"VALID {rule.bundle_id} {rule.bundle_version} ({len(rule.operations)} operations) sha256={rule.sha256}")
    return 0


def _cmd_apply(args) -> int:
    verify = resolve_command(shlex.split(args.verify), Path(os.getcwd())) if args.verify else None
    result = apply_rule(
        args.rule, args.repo, verify_command=verify, write=args.write,
        include_tests=args.include_tests, timeout_s=args.timeout,
    )
    data = result.to_dict()
    if args.json:
        Path(args.json).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    s = data["summary"]
    print(f"Matched: {s['matched']}")
    print(f"Changed: {s['changed']}")
    print(f"Abstained: {s['abstained']}")
    for err in data["rule_errors"]:
        print(f"Rule error: {err}")
    for site in data["sites"]:
        if site["decision"] == "abstained":
            print(f"  abstain {site['file']}:{site['line']} [{site['op_id']}] {site['reason']}")
    for issue in data["file_issues"]:
        print(f"  file issue {issue['file']}: {issue['kind']}: {issue['detail']}")
    if args.diff and data["diff"]:
        print(data["diff"], end="")
    v = data["verification"]
    print("Verification:")
    print(f"  {' '.join(v['command']) or '(none)'}: {v['status'].upper()}")
    print(f"Result: {data['status']} ({data['reason']})")
    print("Written to repository: " + ("yes" if data["written"] else "no (dry run)" if data["dry_run"] else "no"))
    return EXIT_CODES[data["status"]]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="molt", description="Deterministic application of Molt rule bundles.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_val = sub.add_parser("validate", help="validate a rule bundle against the schema")
    p_val.add_argument("rule")
    p_val.set_defaults(func=_cmd_validate)

    p_app = sub.add_parser("apply", help="apply a rule bundle to a repository (dry run by default)")
    p_app.add_argument("rule")
    p_app.add_argument("repo")
    p_app.add_argument("--verify", help='verification command run in a transformed copy, e.g. "python -m pytest -q"')
    p_app.add_argument("--write", action="store_true", help="write changes to REPO, only if the result is PASS")
    p_app.add_argument("--include-tests", action="store_true", help="also transform test files (off by default)")
    p_app.add_argument("--timeout", type=float, default=300, help="verification timeout in seconds")
    p_app.add_argument("--diff", action="store_true", help="print the unified diff")
    p_app.add_argument("--json", help="write the structured result (molt.engine_result.v1) to this path")
    p_app.set_defaults(func=_cmd_apply)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
