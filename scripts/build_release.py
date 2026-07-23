#!/usr/bin/env python3
"""Validate and build the rwskill plugin zip."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


def frontmatter_name(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"\A---\nname:\s*([^\n]+)\n", text)
    if not match:
        raise ValueError(f"invalid frontmatter: {path}")
    return match.group(1).strip()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    repository_check = subprocess.run(
        [sys.executable, str(root / "scripts" / "check_repository.py")],
        capture_output=True,
        text=True,
    )
    if repository_check.returncode:
        print(repository_check.stdout, end="")
        print(repository_check.stderr, end="")
        raise SystemExit("repository check failed")
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    plugin = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if len({version, manifest["version"], plugin["version"]}) != 1:
        raise SystemExit("VERSION, manifest.json, and plugin.json do not match")
    failures: list[str] = []
    release_skills = list(dict.fromkeys(manifest["skills"]))
    for name in release_skills:
        skill = root / "skills" / name
        required = [skill / "SKILL.md", skill / "agents/openai.yaml"]
        if any(not path.is_file() or path.stat().st_size == 0 for path in required):
            failures.append(f"{name}: missing required file")
            continue
        if frontmatter_name(skill / "SKILL.md") != name:
            failures.append(f"{name}: frontmatter name mismatch")
        if "TODO" in (skill / "SKILL.md").read_text(encoding="utf-8"):
            failures.append(f"{name}: TODO remains")
    if failures:
        print(json.dumps({"failures": failures}, ensure_ascii=False, indent=2))
        return 1

    for name in release_skills:
        check = subprocess.run(
            [sys.executable, str(root / "skills" / name / "scripts/self_check.py")],
            capture_output=True,
            text=True,
        )
        if check.returncode:
            print(check.stdout, end="")
            print(check.stderr, end="")
            raise SystemExit(f"standalone research self-check failed: {name}")

    package_name = manifest["name"]
    output = root / "dist" / f"{package_name}-{version}.zip"
    output.parent.mkdir(exist_ok=True)
    include_roots = [root / ".codex-plugin", root / "skills", root / "docs"]
    include_files = [root / "README.md", root / "LICENSE", root / "VERSION", root / "manifest.json"]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for base in include_roots:
            for path in sorted(p for p in base.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"):
                archive.write(path, Path(package_name) / path.relative_to(root))
        for path in include_files:
            archive.write(path, Path(package_name) / path.name)
    print(json.dumps({"version": version, "skills": len(release_skills), "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
