#!/usr/bin/env python3
"""Create, validate, summarize, and gate claim-to-source audits."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "rw-claim-audit/v1"
CLAIM_TYPES = {"quantitative", "categorical", "trend", "comparative", "causal", "method", "interpretive", "other"}
VERDICTS = {"VERIFIED", "PARTIAL", "DISTORTED", "UNSUPPORTED", "UNVERIFIABLE_ACCESS", "NOT_CHECKED", "NOT_APPLICABLE"}
BLOCKING = {"DISTORTED", "UNSUPPORTED"}
REVIEW = {"PARTIAL", "UNVERIFIABLE_ACCESS", "NOT_CHECKED"}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_hash(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("audit root must be an object")
    return data


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_name, path)
    except Exception:
        Path(temp_name).unlink(missing_ok=True)
        raise


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ["schema_version", "document_id", "document_path", "document_hash", "audited_at", "claims"]:
        if field not in data:
            errors.append(f"missing top-level field: {field}")
    if errors:
        return errors
    if data["schema_version"] != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not isinstance(data["claims"], list):
        errors.append("claims must be an array")
        return errors
    seen: set[str] = set()
    for index, claim in enumerate(data["claims"]):
        prefix = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ["id", "text", "location", "claim_type", "source_refs", "verdict", "notes"]:
            if field not in claim:
                errors.append(f"{prefix} missing field: {field}")
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not claim_id.strip():
            errors.append(f"{prefix}.id must be a non-empty string")
        elif claim_id in seen:
            errors.append(f"duplicate claim id: {claim_id}")
        else:
            seen.add(claim_id)
        if claim.get("claim_type") not in CLAIM_TYPES:
            errors.append(f"{prefix}.claim_type is invalid")
        verdict = claim.get("verdict")
        if verdict not in VERDICTS:
            errors.append(f"{prefix}.verdict is invalid")
        refs = claim.get("source_refs")
        if not isinstance(refs, list):
            errors.append(f"{prefix}.source_refs must be an array")
            continue
        for ref_index, ref in enumerate(refs):
            ref_prefix = f"{prefix}.source_refs[{ref_index}]"
            if not isinstance(ref, dict):
                errors.append(f"{ref_prefix} must be an object")
                continue
            for field in ["id", "source_pointer", "locator", "support_note"]:
                if not isinstance(ref.get(field), str) or not ref[field].strip():
                    errors.append(f"{ref_prefix}.{field} must be a non-empty string")
        if verdict in {"VERIFIED", "PARTIAL", "DISTORTED"} and not refs:
            errors.append(f"{prefix} verdict {verdict} requires at least one source_ref")
        if verdict == "UNVERIFIABLE_ACCESS" and not refs:
            errors.append(f"{prefix} UNVERIFIABLE_ACCESS requires a source_ref with the attempted source pointer")
    return errors


def gate_status(data: dict[str, Any]) -> str:
    if not data["claims"]:
        return "REVIEW"
    verdicts = {claim["verdict"] for claim in data["claims"]}
    if verdicts & BLOCKING:
        return "BLOCK"
    if verdicts & REVIEW:
        return "REVIEW"
    return "PASS"


def command_init(args: argparse.Namespace) -> int:
    output = Path(args.output)
    if output.exists() and not args.force:
        print(f"refusing to overwrite existing file: {output}")
        return 2
    document = Path(args.document_path)
    data = {
        "schema_version": SCHEMA_VERSION,
        "document_id": args.document_id,
        "document_path": args.document_path,
        "document_hash": file_hash(document),
        "audited_at": now(),
        "claims": [],
    }
    atomic_write(output, data)
    print(f"created {output}")
    return 0


def command_add_claim(args: argparse.Namespace) -> int:
    path = Path(args.audit)
    data = load(path)
    if any(claim.get("id") == args.id for claim in data.get("claims", []) if isinstance(claim, dict)):
        print(f"duplicate claim id: {args.id}")
        return 2
    data.setdefault("claims", []).append({
        "id": args.id,
        "text": args.text,
        "location": args.location,
        "claim_type": args.claim_type,
        "source_refs": [],
        "verdict": "NOT_CHECKED",
        "notes": "",
    })
    data["audited_at"] = now()
    errors = validate(data)
    if errors:
        print("\n".join(errors))
        return 2
    atomic_write(path, data)
    print(f"added {args.id}")
    return 0


def command_validate(args: argparse.Namespace) -> int:
    try:
        errors = validate(load(Path(args.audit)))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"invalid audit: {exc}")
        return 2
    if errors:
        print("\n".join(errors))
        return 2
    print("claim audit valid")
    return 0


def command_summary(args: argparse.Namespace) -> int:
    data = load(Path(args.audit))
    errors = validate(data)
    if errors:
        print("\n".join(errors))
        return 2
    counts = {verdict: sum(1 for claim in data["claims"] if claim["verdict"] == verdict) for verdict in sorted(VERDICTS)}
    print(json.dumps({"document_id": data["document_id"], "claims": len(data["claims"]), "verdicts": counts, "gate": gate_status(data)}, indent=2))
    return 0


def command_gate(args: argparse.Namespace) -> int:
    data = load(Path(args.audit))
    errors = validate(data)
    if errors:
        print("\n".join(errors))
        return 2
    status = gate_status(data)
    print(status)
    return {"PASS": 0, "REVIEW": 1, "BLOCK": 2}[status]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("output")
    init_parser.add_argument("--document-id", required=True)
    init_parser.add_argument("--document-path", required=True)
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(func=command_init)

    add_parser = subparsers.add_parser("add-claim")
    add_parser.add_argument("audit")
    add_parser.add_argument("--id", required=True)
    add_parser.add_argument("--text", required=True)
    add_parser.add_argument("--location", required=True)
    add_parser.add_argument("--claim-type", choices=sorted(CLAIM_TYPES), required=True)
    add_parser.set_defaults(func=command_add_claim)

    for name, function in [("validate", command_validate), ("summary", command_summary), ("gate", command_gate)]:
        sub = subparsers.add_parser(name)
        sub.add_argument("audit")
        sub.set_defaults(func=function)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
