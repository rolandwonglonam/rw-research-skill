#!/usr/bin/env python3
"""Copy release-approved RW skills from the workspace source tree."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


SYNTHETIC_NOTICE = "> 公开案例使用合成或占位输入，不来自任何个人研究项目。"


def sanitize_public_skill(skill: Path) -> None:
    atoms_path = skill / "references" / "atoms.jsonl"
    if atoms_path.is_file():
        atoms: list[str] = []
        for line in atoms_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            record.pop("original", None)
            atoms.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))
        atoms_path.write_text("\n".join(atoms) + "\n", encoding="utf-8")

    contracts_path = skill / "references" / "behavior-tests.json"
    if contracts_path.is_file():
        contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
        for contract in contracts:
            contract["fixture_kind"] = "synthetic"
        contracts_path.write_text(json.dumps(contracts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    cases_path = skill / "references" / "cases.md"
    if cases_path.is_file():
        text = cases_path.read_text(encoding="utf-8")
        if SYNTHETIC_NOTICE not in text:
            first_line, remainder = text.split("\n", 1)
            text = f"{first_line}\n\n{SYNTHETIC_NOTICE}\n{remainder}"
            cases_path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--only", action="append", default=[], help="copy only the named manifest skill; repeat as needed")
    parser.add_argument("--dry-run", action="store_true", help="report copy and delete actions without changing files")
    args = parser.parse_args()
    plugin_root = Path(__file__).resolve().parents[1]
    source_root = args.source_root or plugin_root.parents[1] / "skills"
    manifest = json.loads((plugin_root / "manifest.json").read_text(encoding="utf-8"))
    target_root = plugin_root / "skills"
    if target_root.is_symlink() or target_root.parent.resolve() != plugin_root.resolve():
        raise SystemExit(f"unsafe target root: {target_root}")
    release_skills = list(dict.fromkeys(manifest["skills"]))
    requested = set(args.only)
    unknown = sorted(requested - set(release_skills))
    if unknown:
        raise SystemExit(f"--only contains skills outside manifest: {', '.join(unknown)}")
    selected = [name for name in release_skills if not requested or name in requested]
    delete_targets = []
    if not requested and target_root.is_dir():
        delete_targets = [existing for existing in target_root.iterdir() if existing.is_dir() and existing.name not in release_skills]
    plan = {
        "dry_run": args.dry_run,
        "source_root": str(source_root),
        "target_root": str(target_root),
        "delete": [path.name for path in delete_targets],
        "copy": selected,
    }
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    target_root.mkdir(exist_ok=True)
    for existing in delete_targets:
        shutil.rmtree(existing)
    copied: list[str] = []
    for name in selected:
        source = source_root / name
        target = target_root / name
        if not (source / "SKILL.md").is_file():
            raise SystemExit(f"missing source skill: {source}")
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
        sanitize_public_skill(target)
        copied.append(name)

    print(json.dumps({**plan, "copied": copied}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
