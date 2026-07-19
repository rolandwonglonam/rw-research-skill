#!/usr/bin/env python3
"""Check the public Skill corpus for personal provenance and research clues."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
ALLOWED_SOURCE_KINDS = {
    "cross_skill_rule",
    "official_public_source",
    "packaged_acceptance",
    "packaged_method",
    "runtime_policy",
}
ALLOWED_PUBLIC_SOURCES = {
    "osf_registrations",
    "privacy_minimization_policy",
    "prospero_eligibility_and_osf_registrations",
    "registration_gate_acceptance",
}
FORBIDDEN_TEXT = {
    "absolute macOS user path": re.compile(r"/Users/[^/\s]+/"),
    "absolute Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\", re.IGNORECASE),
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "personal feedback provenance": re.compile(
        r"用户提供的一组|用户选择先做|用户长期要求|后续用户明确指出|个人文稿或评审记录来自",
        re.IGNORECASE,
    ),
    "private project identifier": re.compile(r"\b(?:HREC|IRB|GRANT)[-_ :#]*\d{3,}\b", re.IGNORECASE),
    "retired topic fixture": re.compile(r"AI 对医学教育|低盐饮食|盐摄入|30 天再入院|死亡率数据库"),
}


def walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in walk_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in walk_strings(item)]
    return []


def scan_text(text: str, label: str, failures: list[str]) -> None:
    for description, pattern in FORBIDDEN_TEXT.items():
        if pattern.search(text):
            failures.append(f"{label}: {description}")


def main() -> int:
    failures: list[str] = []
    atoms = 0
    cases = 0
    contracts = 0
    files = 0

    public_paths = [path for path in SKILLS.rglob("*") if path.is_file()]
    public_paths.extend(path for path in (ROOT / "docs").rglob("*") if path.is_file())
    public_paths.extend(
        [ROOT / "README.md", ROOT / "SKILL.md", ROOT / "manifest.json", ROOT / ".codex-plugin" / "plugin.json"]
    )
    for path in sorted(set(public_paths)):
        if not path.is_file() or path.suffix in {".pyc", ".png", ".jpg", ".jpeg", ".gif", ".pdf"}:
            continue
        files += 1
        relative = str(path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        scan_text(text, relative, failures)

    for path in sorted(SKILLS.glob("*/references/atoms.jsonl")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            atoms += 1
            label = f"{path.relative_to(ROOT)}:{line_number}"
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"{label}: invalid JSON: {exc}")
                continue
            if "original" in record:
                failures.append(f"{label}: raw original field is not public")
            source = record.get("source")
            if not isinstance(source, str) or not (
                source.startswith("packaged_")
                or source.startswith("rw-")
                or source in ALLOWED_PUBLIC_SOURCES
            ):
                failures.append(f"{label}: source is not public or packaged: {source}")
            source_kind = record.get("source_kind")
            if source_kind not in ALLOWED_SOURCE_KINDS:
                failures.append(f"{label}: source_kind is not allowed: {source_kind}")
            for value in walk_strings(record):
                scan_text(value, label, failures)

    for path in sorted(SKILLS.glob("*/references/cases.md")):
        text = path.read_text(encoding="utf-8")
        cases += len(re.findall(r"^## ", text, re.MULTILINE))
        if "公开案例使用合成或占位输入，不来自任何个人研究项目。" not in text:
            failures.append(f"{path.relative_to(ROOT)}: missing synthetic fixture notice")

    for path in sorted(SKILLS.glob("*/references/behavior-tests.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for index, contract in enumerate(data):
            contracts += 1
            if contract.get("fixture_kind") != "synthetic":
                failures.append(f"{path.relative_to(ROOT)}:{index}: fixture_kind must be synthetic")

    result = {
        "files": files,
        "atoms": atoms,
        "cases": cases,
        "contracts": contracts,
        "failures": sorted(set(failures)),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
