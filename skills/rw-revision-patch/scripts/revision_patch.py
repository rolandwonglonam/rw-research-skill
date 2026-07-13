#!/usr/bin/env python3
"""Anchor Markdown blocks and apply hash-checked replacement patches."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_VERSION = "rw-revision-manifest/v1"
PATCH_VERSION = "rw-revision-patch/v1"
MARKER_RE = re.compile(r"^<!--rw-block:(B\d{4,})-->\n", re.MULTILINE)
ANY_MARKER_RE = re.compile(r"<!--rw-block:B\d{4,}-->")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class Block:
    block_id: str
    text: str

    @property
    def block_hash(self) -> str:
        return digest(self.text)


def split_unanchored(text: str) -> list[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if not normalized.strip():
        raise ValueError("document is empty")
    return [part.strip("\n") for part in re.split(r"\n[ \t]*\n+", normalized) if part.strip()]


def parse_anchored(text: str) -> list[Block]:
    matches = list(MARKER_RE.finditer(text))
    if not matches:
        raise ValueError("document has no RW block markers")
    prefix = text[: matches[0].start()]
    if prefix.strip():
        raise ValueError("content appears before first RW block marker")
    blocks: list[Block] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip("\n")
        if not body.strip():
            raise ValueError(f"empty block: {match.group(1)}")
        blocks.append(Block(match.group(1), body))
    if len({block.block_id for block in blocks}) != len(blocks):
        raise ValueError("duplicate block ids in document")
    return blocks


def render(blocks: list[Block]) -> str:
    return "\n\n".join(f"<!--rw-block:{block.block_id}-->\n{block.text}" for block in blocks) + "\n"


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def refuse_same(input_path: Path, output_path: Path) -> None:
    if input_path.resolve() == output_path.resolve():
        raise ValueError("output must differ from input; original files are not overwritten")


def command_anchor(args: argparse.Namespace) -> int:
    source = Path(args.input)
    output = Path(args.output)
    manifest_path = Path(args.manifest)
    refuse_same(source, output)
    if not args.force and (output.exists() or manifest_path.exists()):
        print("refusing to overwrite existing output or manifest; use --force")
        return 2
    raw = source.read_text(encoding="utf-8")
    if ANY_MARKER_RE.search(raw):
        blocks = parse_anchored(raw)
    else:
        blocks = [Block(f"B{index:04d}", part) for index, part in enumerate(split_unanchored(raw), start=1)]
    anchored = render(blocks)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(anchored, encoding="utf-8")
    manifest = {
        "schema_version": MANIFEST_VERSION,
        "source_path": str(source),
        "anchored_path": str(output),
        "base_document_hash": digest(anchored),
        "blocks": [
            {"block_id": block.block_id, "block_hash": block.block_hash, "first_line": block.text.splitlines()[0][:120]}
            for block in blocks
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"anchored {len(blocks)} blocks")
    return 0


def validate_inputs(document: Path, manifest_path: Path, patch_path: Path, allow_large_patch: bool) -> tuple[list[Block], dict[str, Any], dict[str, Any], list[str]]:
    errors: list[str] = []
    document_text = document.read_text(encoding="utf-8")
    blocks = parse_anchored(document_text)
    manifest = read_json(manifest_path)
    patch = read_json(patch_path)
    if manifest.get("schema_version") != MANIFEST_VERSION:
        errors.append("invalid manifest schema_version")
    if patch.get("schema_version") != PATCH_VERSION:
        errors.append("invalid patch schema_version")
    current_hash = digest(document_text)
    if manifest.get("base_document_hash") != current_hash:
        errors.append("manifest base_document_hash does not match document")
    if patch.get("base_document_hash") != current_hash:
        errors.append("patch base_document_hash does not match document")
    manifest_blocks = {item.get("block_id"): item.get("block_hash") for item in manifest.get("blocks", []) if isinstance(item, dict)}
    current_blocks = {block.block_id: block for block in blocks}
    for block in blocks:
        if manifest_blocks.get(block.block_id) != block.block_hash:
            errors.append(f"manifest hash mismatch for {block.block_id}")
    operations = patch.get("operations")
    if not isinstance(operations, list) or not operations:
        errors.append("patch operations must be a non-empty array")
        return blocks, manifest, patch, errors
    seen: set[str] = set()
    for index, operation in enumerate(operations):
        prefix = f"operations[{index}]"
        if not isinstance(operation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if operation.get("op") != "replace":
            errors.append(f"{prefix}.op must be replace")
        block_id = operation.get("block_id")
        if not isinstance(block_id, str) or block_id not in current_blocks:
            errors.append(f"{prefix}.block_id does not exist")
            continue
        if block_id in seen:
            errors.append(f"duplicate operation for {block_id}")
        seen.add(block_id)
        if operation.get("expected_hash") != current_blocks[block_id].block_hash:
            errors.append(f"{prefix}.expected_hash mismatch for {block_id}")
        new_text = operation.get("new_text")
        if not isinstance(new_text, str) or not new_text.strip():
            errors.append(f"{prefix}.new_text must be non-empty")
        elif ANY_MARKER_RE.search(new_text):
            errors.append(f"{prefix}.new_text must not contain RW block markers")
        if not isinstance(operation.get("reason"), str) or not operation["reason"].strip():
            errors.append(f"{prefix}.reason must be non-empty")
        issue_ids = operation.get("issue_ids")
        if not isinstance(issue_ids, list) or not all(isinstance(value, str) for value in issue_ids):
            errors.append(f"{prefix}.issue_ids must be an array of strings")
    touched_ratio = len(seen) / len(blocks)
    if touched_ratio > 0.60 and not allow_large_patch:
        errors.append(f"patch touches {touched_ratio:.1%} of blocks; explicit --allow-large-patch required above 60%")
    return blocks, manifest, patch, errors


def command_check(args: argparse.Namespace) -> int:
    try:
        blocks, _, _, errors = validate_inputs(Path(args.document), Path(args.manifest), Path(args.patch), args.allow_large_patch)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"check failed: {exc}")
        return 2
    if errors:
        print("\n".join(errors))
        return 2
    print(f"patch valid for {len(blocks)} blocks")
    return 0


def command_apply(args: argparse.Namespace) -> int:
    document = Path(args.document)
    output = Path(args.output)
    refuse_same(document, output)
    report_path = Path(args.report)
    if not args.force and (output.exists() or report_path.exists()):
        print("refusing to overwrite existing output or report; use --force")
        return 2
    try:
        blocks, _, patch, errors = validate_inputs(document, Path(args.manifest), Path(args.patch), args.allow_large_patch)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"apply failed: {exc}")
        return 2
    if errors:
        print("\n".join(errors))
        return 2
    operations = {operation["block_id"]: operation for operation in patch["operations"]}
    revised: list[Block] = []
    changes: list[dict[str, Any]] = []
    for block in blocks:
        operation = operations.get(block.block_id)
        if operation is None:
            revised.append(block)
            continue
        new_block = Block(block.block_id, operation["new_text"].strip("\n"))
        revised.append(new_block)
        changes.append({
            "block_id": block.block_id,
            "old_hash": block.block_hash,
            "new_hash": new_block.block_hash,
            "reason": operation["reason"],
            "issue_ids": operation["issue_ids"],
        })
    revised_text = render(revised)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(revised_text, encoding="utf-8")
    preserved = len(blocks) - len(changes)
    report = {
        "schema_version": "rw-revision-report/v1",
        "base_document_hash": digest(document.read_text(encoding="utf-8")),
        "revised_document_hash": digest(revised_text),
        "total_blocks": len(blocks),
        "changed_blocks": len(changes),
        "preserved_blocks": preserved,
        "preserved_ratio": preserved / len(blocks),
        "changes": changes,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"applied {len(changes)} changes; preserved {preserved}/{len(blocks)} blocks")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    anchor = subparsers.add_parser("anchor")
    anchor.add_argument("input")
    anchor.add_argument("--output", required=True)
    anchor.add_argument("--manifest", required=True)
    anchor.add_argument("--force", action="store_true")
    anchor.set_defaults(func=command_anchor)
    for name, function in [("check", command_check), ("apply", command_apply)]:
        sub = subparsers.add_parser(name)
        sub.add_argument("document")
        sub.add_argument("--manifest", required=True)
        sub.add_argument("--patch", required=True)
        sub.add_argument("--allow-large-patch", action="store_true")
        if name == "apply":
            sub.add_argument("--output", required=True)
            sub.add_argument("--report", required=True)
            sub.add_argument("--force", action="store_true")
        sub.set_defaults(func=function)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
