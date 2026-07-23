#!/usr/bin/env python3
"""Validate and merge controlled-vocabulary verification records."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


VOCABULARIES = {"mesh", "emtree", "cinahl", "apa"}
STATUSES = {
    "verified_by_public_api",
    "verified_in_subscribed_platform",
    "user_confirmed",
    "candidate",
    "unverified",
    "rejected",
}
VERIFIED_STATUSES = {
    "verified_by_public_api",
    "verified_in_subscribed_platform",
    "user_confirmed",
}


def load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_record(row: dict[str, Any], concept_ids: set[str]) -> list[str]:
    errors: list[str] = []
    concept_id = str(row.get("concept_id", "")).strip()
    vocabulary = str(row.get("vocabulary", "")).strip().lower()
    status = str(row.get("status", "candidate")).strip()
    if concept_id not in concept_ids:
        errors.append(f"unknown concept_id: {concept_id or '[missing]'}")
    if vocabulary not in VOCABULARIES:
        errors.append(f"unsupported vocabulary: {vocabulary or '[missing]'}")
    if not str(row.get("label", "")).strip():
        errors.append("label is required")
    if status not in STATUSES:
        errors.append(f"unsupported status: {status}")
    if vocabulary != "mesh" and status == "verified_by_public_api":
        errors.append(f"{vocabulary} cannot use verified_by_public_api")
    if status in VERIFIED_STATUSES:
        if not str(row.get("source", "")).strip():
            errors.append("verified record requires source")
        if not str(row.get("verified_at", "")).strip():
            errors.append("verified record requires verified_at")
    return errors


def merge(strategy: dict[str, Any], records: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    result = deepcopy(strategy)
    concepts = {str(row.get("id")): row for row in result.get("concepts", [])}
    failures: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    replaced = 0
    for index, raw in enumerate(records, 1):
        row = dict(raw)
        row["vocabulary"] = str(row.get("vocabulary", "")).lower()
        row.setdefault("status", "candidate")
        row.setdefault("explode", True)
        row.setdefault("focus", False)
        errors = validate_record(row, set(concepts))
        if errors:
            failures.append({"index": index, "record": raw, "errors": errors})
            continue
        concept = concepts[row["concept_id"]]
        headings = concept.setdefault("headings", {}).setdefault(row["vocabulary"], [])
        candidate = {key: value for key, value in row.items() if key not in {"concept_id", "vocabulary"}}
        key = (str(candidate.get("identifier") or ""), str(candidate["label"]).casefold())
        match_index = next(
            (
                position
                for position, existing in enumerate(headings)
                if (
                    str(existing.get("identifier") or "") if isinstance(existing, dict) else "",
                    str(existing.get("label") if isinstance(existing, dict) else existing).casefold(),
                )
                == key
            ),
            None,
        )
        if match_index is None:
            headings.append(candidate)
        else:
            headings[match_index] = candidate
            replaced += 1
        accepted.append(row)
    report = {
        "accepted": len(accepted),
        "rejected": len(failures),
        "replaced": replaced,
        "failures": failures,
    }
    return result, report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--records", required=True)
    parser.add_argument("--output")
    parser.add_argument("--report")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        strategy = load_json(args.strategy)
        payload = load_json(args.records)
        records = payload.get("records", []) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("records must be a list")
        merged, report = merge(strategy, records)
        if args.report:
            Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.dry_run:
            sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        elif args.output:
            Path(args.output).write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            sys.stdout.write(json.dumps({"strategy": merged, "report": report}, ensure_ascii=False, indent=2) + "\n")
        return 1 if report["rejected"] else 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
