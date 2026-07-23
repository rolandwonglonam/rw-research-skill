#!/usr/bin/env python3
"""Build and validate an experimental RW Paper Case from one user-provided PDF."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any

import fitz
from PIL import Image


SCHEMA = "rw-paper-case/v0-experimental"
CONFIG = {
    "text_backend": "pymupdf-layout-profile-v2",
    "visual_backend": "pymupdf-rendered-regions-v2",
    "heading_rules_version": "2026-07-23.2",
    "table_stitch_version": "2026-07-23.1",
    "min_visual_area_ratio": 0.012,
    "max_visual_area_ratio": 0.82,
    "render_scale": 2.0,
    "heading_size_delta": 1.0,
    "heading_bold_ratio": 0.6,
    "table_bottom_ratio": 0.84,
    "continuation_top_ratio": 0.34,
    "continuation_min_rows": 2,
}
STAGES = (
    "source_fixed",
    "content_located",
    "research_structure",
    "visual_evidence",
    "claim_candidates",
    "report_assembled",
    "claim_gate",
)
REPORT_STAGES = (
    ("01-question.md", "研究问题与论文身份", "只记录题名、稳定标识、研究问题、研究设计和对应 locator。"),
    ("02-methods.md", "方法", "记录样本、分组、干预或暴露、测量、分析方法及对应 locator。"),
    ("03-results-and-visuals.md", "结果与视觉证据", "分开记录主要、次要和安全结果；审核每个图表候选。"),
    ("04-limits.md", "限制与适用边界", "区分作者报告的限制、当前推断和不能外推的人群。"),
    ("05-conclusion.md", "结论", "只汇总前四阶段已有证据，不增加新事实。"),
)
AUDIT_VERDICTS = {"VERIFIED", "PARTIAL", "DISTORTED", "UNSUPPORTED", "UNVERIFIABLE_ACCESS", "NOT_CHECKED", "NOT_APPLICABLE"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def paper_id(doi: str, source_hash: str, zotero_library_id: int | None, zotero_key: str) -> str:
    if zotero_library_id is not None and zotero_key:
        return f"zotero-{zotero_library_id}-{zotero_key}"
    if doi:
        safe_doi = re.sub(r"[^a-z0-9._-]+", "-", doi.casefold()).strip("-")
        return f"doi-{safe_doi}"
    return f"sha256-{source_hash[:16]}"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


SECTION_TERMS = {
    "abstract",
    "background",
    "objective",
    "objectives",
    "aim",
    "aims",
    "introduction",
    "method",
    "methods",
    "materials and methods",
    "patients and methods",
    "results",
    "findings",
    "discussion",
    "conclusion",
    "conclusions",
    "limitations",
    "references",
    "acknowledgments",
    "acknowledgements",
    "funding",
    "conflicts of interest",
    "data availability",
}
STRUCTURE_START_TERMS = {"abstract", "background", "introduction", "method", "methods", "materials and methods", "patients and methods", "results"}
METADATA_PREFIX = re.compile(
    r"^(publication date|published|received|accepted|doi|pmid|keywords?|key words)(?:\s*[:：])?(?:\s|$)",
    re.I,
)
CAPTION_PREFIX = re.compile(r"^(table|fig(?:ure)?\.?)\s*(?:s?\d+|[ivxlcdm]+)\b", re.I)


def body_font_size(document: fitz.Document) -> float:
    counts: Counter[float] = Counter()
    for page in document:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = normalized(str(span.get("text", "")))
                    size = round(float(span.get("size", 0.0)), 1)
                    if text and 7.0 <= size <= 16.0:
                        counts[size] += len(text)
    return counts.most_common(1)[0][0] if counts else 11.0


def block_profile(block: dict[str, Any]) -> tuple[str, float, float]:
    spans = [span for line in block.get("lines", []) for span in line.get("spans", [])]
    text = normalized(" ".join(str(span.get("text", "")) for span in spans))
    visible = [(span, len(normalized(str(span.get("text", ""))))) for span in spans]
    total_chars = sum(length for _, length in visible) or 1
    bold_chars = sum(
        length
        for span, length in visible
        if "bold" in str(span.get("font", "")).lower() or int(span.get("flags", 0)) & 16
    )
    max_size = max((float(span.get("size", 0.0)) for span in spans), default=0.0)
    return text, max_size, bold_chars / total_chars


def heading_profile(text: str, max_size: float, bold_ratio: float, body_size: float) -> dict[str, Any] | None:
    line = normalized(text)
    if not line or len(line) > 110:
        return None
    if METADATA_PREFIX.match(line) or CAPTION_PREFIX.match(line):
        return None
    canonical = re.sub(r"[:：]$", "", line).strip().casefold()
    if canonical in SECTION_TERMS:
        return {"basis": "section_term", "confidence": 0.99, "term": canonical}
    if re.search(r"[.!?;。！？；]$", line) or re.search(r"\b\d+\s*/\s*\d+\b", line):
        return None
    typographic = max_size >= body_size + CONFIG["heading_size_delta"] and bold_ratio >= CONFIG["heading_bold_ratio"]
    numbered = bool(re.match(r"^\d+(?:\.\d+)*(?:[.)])?\s+\S", line))
    word_count = len(line.split())
    if typographic and word_count <= 14:
        return {
            "basis": "numbered_typography" if numbered else "typography",
            "confidence": 0.96 if numbered else 0.9,
        }
    return None


def extract_text_units(document: fitz.Document) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    units: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    body_size = body_font_size(document)
    structure_started = False
    for page_index, page in enumerate(document, start=1):
        blocks = page.get_text("dict", sort=True).get("blocks", [])
        text_index = 0
        for block in blocks:
            if int(block.get("type", 0)) != 0:
                continue
            text, max_size, bold_ratio = block_profile(block)
            if not text:
                continue
            text_index += 1
            unit_id = f"p{page_index:03d}-t{text_index:03d}"
            bbox = [round(float(value), 2) for value in block.get("bbox", (0, 0, 0, 0))]
            heading = heading_profile(text, max_size, bold_ratio, body_size)
            if heading and heading.get("term") in STRUCTURE_START_TERMS:
                structure_started = True
            if heading and heading["basis"] != "section_term" and not structure_started:
                heading = None
            if CAPTION_PREFIX.match(text):
                kind = "caption"
            else:
                kind = "heading" if heading else "paragraph"
            row = {
                "id": unit_id,
                "kind": kind,
                "page": page_index,
                "bbox": bbox,
                "text": text,
                "locator": f"p. {page_index}, text unit {unit_id}",
            }
            if heading:
                row["heading_basis"] = heading["basis"]
                row["heading_confidence"] = heading["confidence"]
            units.append(row)
            if kind == "heading":
                sections.append(
                    {
                        "text_unit_id": unit_id,
                        "page": page_index,
                        "heading": text,
                        "basis": heading["basis"],
                        "confidence": heading["confidence"],
                    }
                )
    return units, sections


def bbox_iou(first: fitz.Rect, second: fitz.Rect) -> float:
    overlap = first & second
    if overlap.is_empty:
        return 0.0
    union = first.get_area() + second.get_area() - overlap.get_area()
    return overlap.get_area() / union if union else 0.0


def caption_for(page: fitz.Page, target: fitz.Rect) -> str:
    candidates: list[tuple[float, str]] = []
    for block in page.get_text("blocks", sort=True):
        if len(block) < 7 or int(block[6]) != 0:
            continue
        text = normalized(str(block[4]))
        if not re.match(r"^(fig(?:ure)?\.?|table)\s*\d+", text, re.I):
            continue
        rect = fitz.Rect(block[:4])
        vertical = min(abs(rect.y0 - target.y1), abs(target.y0 - rect.y1))
        horizontal_overlap = max(0.0, min(rect.x1, target.x1) - max(rect.x0, target.x0))
        if vertical <= 90 and horizontal_overlap > 0:
            candidates.append((vertical, text))
    return min(candidates, default=(0.0, ""), key=lambda item: item[0])[1]


def visual_candidates(page: fitz.Page) -> list[tuple[str, fitz.Rect, str]]:
    candidates: list[tuple[str, fitz.Rect, str]] = []
    page_area = page.rect.get_area() or 1.0

    try:
        tables = page.find_tables()
    except Exception:
        tables = []
    for table in tables:
        rect = fitz.Rect(table.bbox)
        ratio = rect.get_area() / page_area
        if CONFIG["min_visual_area_ratio"] <= ratio <= CONFIG["max_visual_area_ratio"]:
            candidates.append(("table", rect, caption_for(page, rect)))

    try:
        images = page.get_image_info(xrefs=True)
    except Exception:
        images = []
    for info in images:
        rect = fitz.Rect(info.get("bbox", (0, 0, 0, 0)))
        ratio = rect.get_area() / page_area
        if rect.width < 70 or rect.height < 55:
            continue
        if not CONFIG["min_visual_area_ratio"] <= ratio <= CONFIG["max_visual_area_ratio"]:
            continue
        if any(bbox_iou(rect, existing[1]) >= 0.8 for existing in candidates):
            continue
        candidates.append(("figure", rect, caption_for(page, rect)))
    return candidates


def horizontal_overlap_ratio(first: fitz.Rect, second: fitz.Rect) -> float:
    overlap = max(0.0, min(first.x1, second.x1) - max(first.x0, second.x0))
    return overlap / min(first.width, second.width) if min(first.width, second.width) else 0.0


def continuation_bbox_from_words(page: fitz.Page, previous: fitz.Rect, col_count: int) -> fitz.Rect | None:
    groups: dict[int, list[tuple[Any, ...]]] = defaultdict(list)
    for word in page.get_text("words", sort=True):
        if len(word) >= 8:
            groups[int(word[5])].append(word)

    candidates: list[fitz.Rect] = []
    required_columns = max(3, min(5, col_count - 1))
    for words in groups.values():
        rect = fitz.Rect(
            min(float(word[0]) for word in words),
            min(float(word[1]) for word in words),
            max(float(word[2]) for word in words),
            max(float(word[3]) for word in words),
        )
        if rect.y0 > page.rect.height * CONFIG["continuation_top_ratio"]:
            continue
        if horizontal_overlap_ratio(rect, previous) < 0.72:
            continue
        columns = len({int(word[6]) for word in words})
        numeric_tokens = sum(bool(re.search(r"\d", str(word[4]))) for word in words)
        if columns >= required_columns and numeric_tokens >= required_columns - 1:
            candidates.append(rect)

    candidates.sort(key=lambda rect: rect.y0)
    if len(candidates) < CONFIG["continuation_min_rows"]:
        return None
    if candidates[0].y0 > page.rect.height * 0.22:
        return None

    run = [candidates[0]]
    for rect in candidates[1:]:
        if rect.y0 - run[-1].y1 > 58:
            break
        run.append(rect)
    if len(run) < CONFIG["continuation_min_rows"]:
        return None
    return fitz.Rect(previous.x0, max(0.0, run[0].y0 - 4), previous.x1, min(page.rect.y1, run[-1].y1 + 4))


def page_tables(page: fitz.Page) -> list[dict[str, Any]]:
    try:
        finder = page.find_tables()
        tables = list(finder.tables)
    except Exception:
        tables = []
    rows = []
    page_area = page.rect.get_area() or 1.0
    for table in tables:
        rect = fitz.Rect(table.bbox)
        ratio = rect.get_area() / page_area
        if CONFIG["min_visual_area_ratio"] <= ratio <= CONFIG["max_visual_area_ratio"]:
            rows.append({"rect": rect, "caption": caption_for(page, rect), "col_count": int(table.col_count)})
    return rows


def collect_table_visuals(document: fitz.Document) -> tuple[list[dict[str, Any]], set[tuple[int, int]]]:
    tables_by_page = [page_tables(page) for page in document]
    consumed: set[tuple[int, int]] = set()
    visuals: list[dict[str, Any]] = []
    for page_zero, tables in enumerate(tables_by_page):
        for table_index, table in enumerate(tables):
            if (page_zero, table_index) in consumed:
                continue
            segments = [{"page": page_zero + 1, "rect": table["rect"]}]
            current_page = page_zero
            current_rect = table["rect"]
            col_count = table["col_count"]
            while current_page + 1 < len(document):
                if current_rect.y1 < document[current_page].rect.height * CONFIG["table_bottom_ratio"]:
                    break
                next_page = current_page + 1
                match_index = None
                for candidate_index, candidate in enumerate(tables_by_page[next_page]):
                    if (next_page, candidate_index) in consumed:
                        continue
                    if candidate["rect"].y0 <= document[next_page].rect.height * 0.22 and horizontal_overlap_ratio(current_rect, candidate["rect"]) >= 0.72:
                        match_index = candidate_index
                        break
                if match_index is not None:
                    candidate = tables_by_page[next_page][match_index]
                    consumed.add((next_page, match_index))
                    current_rect = candidate["rect"]
                    col_count = candidate["col_count"]
                else:
                    continuation = continuation_bbox_from_words(document[next_page], current_rect, col_count)
                    if continuation is None:
                        break
                    current_rect = continuation
                segments.append({"page": next_page + 1, "rect": current_rect})
                current_page = next_page
            visuals.append({"kind": "table", "caption": table["caption"], "segments": segments})
    return visuals, consumed


def render_segments(document: fitz.Document, segments: list[dict[str, Any]], image_path: Path) -> None:
    rendered: list[Image.Image] = []
    matrix = fitz.Matrix(CONFIG["render_scale"], CONFIG["render_scale"])
    for segment in segments:
        pixmap = document[int(segment["page"]) - 1].get_pixmap(matrix=matrix, clip=segment["rect"], alpha=False)
        with Image.open(BytesIO(pixmap.tobytes("png"))) as image:
            rendered.append(image.convert("RGB").copy())
    if len(rendered) == 1:
        rendered[0].save(image_path)
        return
    seam = 8
    width = max(image.width for image in rendered)
    height = sum(image.height for image in rendered) + seam * (len(rendered) - 1)
    stitched = Image.new("RGB", (width, height), "white")
    y = 0
    for index, image in enumerate(rendered):
        stitched.paste(image, (0, y))
        y += image.height
        if index < len(rendered) - 1:
            stitched.paste((176, 176, 176), (0, y, width, y + seam))
            y += seam
    stitched.save(image_path)


def extract_visual_evidence(document: fitz.Document, output_dir: Path) -> list[dict[str, Any]]:
    visuals_dir = output_dir / "visuals"
    visuals_dir.mkdir(parents=True, exist_ok=True)
    table_visuals, _ = collect_table_visuals(document)
    candidates = list(table_visuals)
    table_segments = [segment for visual in table_visuals for segment in visual["segments"]]
    for page_index, page in enumerate(document, start=1):
        for kind, rect, caption in visual_candidates(page):
            if kind == "table":
                continue
            if any(segment["page"] == page_index and bbox_iou(segment["rect"], rect) >= 0.8 for segment in table_segments):
                continue
            candidates.append({"kind": kind, "caption": caption, "segments": [{"page": page_index, "rect": rect}]})
    candidates.sort(key=lambda item: (item["segments"][0]["page"], item["segments"][0]["rect"].y0))

    rows: list[dict[str, Any]] = []
    counters: Counter[int] = Counter()
    for candidate in candidates:
        segments = candidate["segments"]
        first_page = int(segments[0]["page"])
        counters[first_page] += 1
        visual_id = f"p{first_page:03d}-v{counters[first_page]:02d}"
        page_suffix = f"-p{int(segments[-1]['page']):03d}" if len(segments) > 1 else ""
        image_path = visuals_dir / f"{visual_id}{page_suffix}-{candidate['kind']}.png"
        render_segments(document, segments, image_path)
        segment_rows = []
        locators = []
        for segment in segments:
            rect = segment["rect"]
            page_number = int(segment["page"])
            bbox = [round(value, 2) for value in (rect.x0, rect.y0, rect.x1, rect.y1)]
            locator = f"p. {page_number}, bbox {rect.x0:.1f},{rect.y0:.1f},{rect.x1:.1f},{rect.y1:.1f}"
            segment_rows.append({"page": page_number, "bbox": bbox, "locator": locator})
            locators.append(locator)
        first = segment_rows[0]
        rows.append(
            {
                "id": visual_id,
                "kind": candidate["kind"],
                "page": first["page"],
                "pages": [segment["page"] for segment in segment_rows],
                "bbox": first["bbox"],
                "segments": segment_rows,
                "caption": candidate["caption"],
                "image": image_path.relative_to(output_dir).as_posix(),
                "image_sha256": sha256_file(image_path),
                "locator": "; ".join(locators),
                "cross_page": len(segment_rows) > 1,
                "review_status": "needs_human_review",
            }
        )
    return rows


def build_case(args: argparse.Namespace) -> int:
    pdf = args.pdf.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    output.mkdir(parents=True, exist_ok=True)

    source_hash = sha256_file(pdf)
    config_hash = json_hash(CONFIG)
    document = fitz.open(pdf)
    text_units, sections = extract_text_units(document)
    visuals = extract_visual_evidence(document, output)

    source_manifest: dict[str, Any] = {
        "schema": "rw-paper-source/v0-experimental",
        "pdf_path": str(pdf),
        "pdf_sha256": source_hash,
        "pages": document.page_count,
        "title": args.title,
        "doi": args.doi,
        "access": "user-provided-file",
    }
    if args.zotero_library_id is not None or args.zotero_key or args.zotero_attachment_key:
        source_manifest["optional_zotero"] = {
            "library_id": args.zotero_library_id,
            "item_key": args.zotero_key,
            "attachment_key": args.zotero_attachment_key,
        }
    case = {
        "schema": SCHEMA,
        "created_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "paper_id": paper_id(args.doi, source_hash, args.zotero_library_id, args.zotero_key),
        "source_hash": source_hash,
        "config_hash": config_hash,
        "source_manifest": "source-manifest.json",
        "artifacts": {
            "text_units": "evidence/text-units.jsonl",
            "section_map": "evidence/section-map.json",
            "visual_evidence": "evidence/visual-evidence.jsonl",
            "claim_candidates": "evidence/claim-candidates.jsonl",
            "report": "report.md",
            "claim_audit": "audit/claim-audit.json",
            "litnet_preview": "litnet-writeback-preview.json",
        },
        "counts": {"text_units": len(text_units), "sections": len(sections), "visuals": len(visuals)},
        "privacy": {"external_model_called": False, "pdf_copied": False},
    }
    stage_state = {
        "schema": "rw-paper-stage-state/v0-experimental",
        "source_hash": source_hash,
        "config_hash": config_hash,
        "stages": {
            stage: {
                "status": "complete" if stage in {"source_fixed", "content_located", "visual_evidence"} else "pending",
                "source_hash": source_hash,
                "config_hash": config_hash,
            }
            for stage in STAGES
        },
    }

    write_json(output / "source-manifest.json", source_manifest)
    write_json(output / "case.json", case)
    write_json(output / "stage-state.json", stage_state)
    write_json(output / "evidence" / "section-map.json", {"sections": sections})
    write_jsonl(output / "evidence" / "text-units.jsonl", text_units)
    write_jsonl(output / "evidence" / "visual-evidence.jsonl", visuals)
    write_jsonl(output / "evidence" / "claim-candidates.jsonl", [])
    (output / "audit").mkdir(exist_ok=True)
    print(json.dumps(case["counts"], ensure_ascii=False))
    return 0


def scaffold_command(args: argparse.Namespace) -> int:
    output = args.output.expanduser().resolve()
    problems = validate_case(output)
    if problems:
        raise ValueError("cannot scaffold an invalid or stale case: " + "; ".join(problems))
    case = json.loads((output / "case.json").read_text(encoding="utf-8"))
    source = json.loads((output / "source-manifest.json").read_text(encoding="utf-8"))
    stages_dir = output / "stages"
    stages_dir.mkdir(exist_ok=True)
    created: list[str] = []
    for filename, heading, instruction in REPORT_STAGES:
        path = stages_dir / filename
        if path.exists() and not args.force:
            continue
        path.write_text(
            f"# {heading}\n\n"
            f"论文：{source.get('title', '')}\n\n"
            f"Paper Case：`{case['paper_id']}`\n\n"
            f"来源 hash：`{case['source_hash']}`\n\n"
            f"## 写作约束\n\n{instruction}\n\n"
            "## 内容\n\n［待填写］\n\n"
            "## 证据定位\n\n［填写 text unit、page、table、figure 或 supplement locator］\n",
            encoding="utf-8",
        )
        created.append(path.relative_to(output).as_posix())
    report = output / "report.md"
    if not report.exists() or args.force:
        sections = "\n".join(
            f"## {index}．{heading}\n\n见 `stages/{filename}`。\n"
            for index, (filename, heading, _) in enumerate(REPORT_STAGES, start=1)
        )
        report.write_text(
            f"# {source.get('title', '')}｜分阶段精读报告\n\n"
            "> 状态：草稿。阶段文件完成并通过 Claim Audit 前，不进入已验证结论。\n\n"
            + sections,
            encoding="utf-8",
        )
        created.append("report.md")
    print(json.dumps({"paper_id": case["paper_id"], "created": created}, ensure_ascii=False))
    return 0


def mark_stage_command(args: argparse.Namespace) -> int:
    output = args.output.expanduser().resolve()
    artifact = (output / args.artifact).resolve()
    try:
        artifact_relative = artifact.relative_to(output)
    except ValueError as exc:
        raise ValueError("stage artifact must stay inside the Paper Case") from exc
    if not artifact.is_file():
        raise FileNotFoundError(artifact)
    state_path = output / "stage-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    upstream_artifacts = []
    for value in args.upstream:
        path = (output / value).resolve()
        try:
            relative = path.relative_to(output)
        except ValueError as exc:
            raise ValueError("upstream artifact must stay inside the Paper Case") from exc
        if not path.is_file():
            raise FileNotFoundError(path)
        upstream_artifacts.append({"path": relative.as_posix(), "sha256": sha256_file(path)})
    state["stages"][args.stage] = {
        "status": args.status,
        "source_hash": state["source_hash"],
        "config_hash": state["config_hash"],
        "artifact": artifact_relative.as_posix(),
        "artifact_sha256": sha256_file(artifact),
        "upstream_artifacts": upstream_artifacts,
    }
    write_json(state_path, state)
    print(json.dumps({"stage": args.stage, "status": args.status, "artifact": artifact_relative.as_posix()}, ensure_ascii=False))
    return 0


def claim_gate(audit: dict[str, Any]) -> tuple[str, dict[str, int]]:
    blocking = {"DISTORTED", "UNSUPPORTED"}
    review = {"PARTIAL", "UNVERIFIABLE_ACCESS", "NOT_CHECKED"}
    counts: Counter[str] = Counter(str(claim.get("verdict", "NOT_CHECKED")) for claim in audit.get("claims", []))
    verdicts = set(counts)
    if verdicts & blocking:
        return "BLOCK", dict(sorted(counts.items()))
    if not audit.get("claims") or verdicts & review:
        return "REVIEW", dict(sorted(counts.items()))
    return "PASS", dict(sorted(counts.items()))


def validate_claim_audit(audit: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    claims = audit.get("claims")
    if not isinstance(claims, list):
        return ["claim audit claims must be an array"]
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            problems.append(f"claim {index} must be an object")
            continue
        verdict = claim.get("verdict")
        if verdict not in AUDIT_VERDICTS:
            problems.append(f"claim {index} has an invalid verdict")
        refs = claim.get("source_refs")
        if not isinstance(refs, list):
            problems.append(f"claim {index} source_refs must be an array")
        elif verdict in {"VERIFIED", "PARTIAL", "DISTORTED"} and not refs:
            problems.append(f"claim {index} verdict {verdict} requires source_refs")
    return problems


def litnet_preview_command(args: argparse.Namespace) -> int:
    output = args.output.expanduser().resolve()
    problems = validate_case(output)
    if problems:
        raise ValueError("cannot preview an invalid or stale case: " + "; ".join(problems))
    audit_path = args.claim_audit.expanduser().resolve()
    if not audit_path.is_file():
        raise FileNotFoundError(audit_path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("schema_version") != "rw-claim-audit/v1":
        raise ValueError("claim audit schema must be rw-claim-audit/v1")
    audit_problems = validate_claim_audit(audit)
    if audit_problems:
        raise ValueError("invalid claim audit: " + "; ".join(audit_problems))
    document = Path(str(audit.get("document_path", "")))
    if not document.is_absolute():
        document = audit_path.parent / document
    if not document.is_file() or sha256_file(document) != audit.get("document_hash"):
        raise ValueError("claim audit document is missing or changed")
    gate, verdicts = claim_gate(audit)
    case = json.loads((output / "case.json").read_text(encoding="utf-8"))
    preview = {
        "schema": "rw-litnet-paper-case-preview/v1",
        "mode": "preview_only",
        "paper_case": case["paper_id"],
        "source_sha256": case["source_hash"],
        "deep_read_status": "audited" if gate == "PASS" else "review_required",
        "claim_gate": gate,
        "claim_verdicts": verdicts,
        "verified_claim_count": verdicts.get("VERIFIED", 0),
        "target_work": args.litnet_work,
        "target_zotero_record": args.zotero_record,
        "proposed_links": {
            "report": case["artifacts"]["report"],
            "claim_audit": str(audit_path),
            "visual_evidence": case["artifacts"]["visual_evidence"],
        },
        "write_performed": False,
    }
    preview_path = output / case["artifacts"]["litnet_preview"]
    write_json(preview_path, preview)
    print(json.dumps({"preview": str(preview_path), "claim_gate": gate}, ensure_ascii=False))
    return 0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_case(output: Path) -> list[str]:
    problems: list[str] = []
    case_path = output / "case.json"
    source_path = output / "source-manifest.json"
    if not case_path.exists() or not source_path.exists():
        return ["missing case.json or source-manifest.json"]
    case = json.loads(case_path.read_text(encoding="utf-8"))
    source = json.loads(source_path.read_text(encoding="utf-8"))
    pdf = Path(source["pdf_path"])
    if not pdf.exists():
        problems.append("source PDF is missing")
    elif sha256_file(pdf) != case["source_hash"]:
        problems.append("source PDF hash changed; case is STALE")
    if json_hash(CONFIG) != case["config_hash"]:
        problems.append("extractor config changed; case is STALE")

    pages = int(source.get("pages", 0))
    for row in load_jsonl(output / case["artifacts"]["text_units"]):
        if not 1 <= int(row.get("page", 0)) <= pages:
            problems.append(f"invalid text locator: {row.get('id')}")
    for row in load_jsonl(output / case["artifacts"]["visual_evidence"]):
        image = output / row.get("image", "")
        if not image.exists():
            problems.append(f"missing visual image: {row.get('id')}")
        elif sha256_file(image) != row.get("image_sha256"):
            problems.append(f"visual hash changed: {row.get('id')}")
        if not row.get("locator"):
            problems.append(f"visual has no locator: {row.get('id')}")
        segments = row.get("segments", [])
        if not segments:
            problems.append(f"visual has no source segments: {row.get('id')}")
        for segment in segments:
            if not 1 <= int(segment.get("page", 0)) <= pages:
                problems.append(f"invalid visual segment page: {row.get('id')}")
            if len(segment.get("bbox", [])) != 4 or not segment.get("locator"):
                problems.append(f"invalid visual segment locator: {row.get('id')}")
        if bool(row.get("cross_page")) != (len(segments) > 1):
            problems.append(f"visual cross-page flag mismatch: {row.get('id')}")

    stage_path = output / "stage-state.json"
    if stage_path.exists():
        stage_state = json.loads(stage_path.read_text(encoding="utf-8"))
        for stage, record in stage_state.get("stages", {}).items():
            artifact_name = record.get("artifact")
            artifact_hash = record.get("artifact_sha256")
            if not artifact_name or not artifact_hash:
                continue
            artifact = output / artifact_name
            if not artifact.exists():
                problems.append(f"missing stage artifact: {stage}")
            elif sha256_file(artifact) != artifact_hash:
                problems.append(f"stage artifact changed; downstream is STALE: {stage}")
            for upstream in record.get("upstream_artifacts", []):
                upstream_path = output / upstream.get("path", "")
                if not upstream_path.is_file():
                    problems.append(f"missing upstream artifact; stage is STALE: {stage}")
                elif sha256_file(upstream_path) != upstream.get("sha256"):
                    problems.append(f"upstream artifact changed; stage is STALE: {stage}")
    return sorted(set(problems))


def validate_command(args: argparse.Namespace) -> int:
    output = args.output.expanduser().resolve()
    problems = validate_case(output)
    if problems:
        print("Validation failed:")
        for problem in problems:
            print(f"- {problem}")
        return 2
    print("Validation passed")
    return 0


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--pdf", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--title", required=True)
    build.add_argument("--doi", default="")
    build.add_argument("--zotero-library-id", type=int)
    build.add_argument("--zotero-key", default="")
    build.add_argument("--zotero-attachment-key", default="")
    build.set_defaults(func=build_case)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--output", type=Path, required=True)
    validate.set_defaults(func=validate_command)
    scaffold = subparsers.add_parser("scaffold")
    scaffold.add_argument("--output", type=Path, required=True)
    scaffold.add_argument("--force", action="store_true")
    scaffold.set_defaults(func=scaffold_command)
    mark_stage = subparsers.add_parser("mark-stage")
    mark_stage.add_argument("--output", type=Path, required=True)
    mark_stage.add_argument("--stage", choices=STAGES, required=True)
    mark_stage.add_argument("--artifact", required=True)
    mark_stage.add_argument("--upstream", action="append", default=[])
    mark_stage.add_argument("--status", choices=("complete", "pass", "review", "block"), default="complete")
    mark_stage.set_defaults(func=mark_stage_command)
    litnet = subparsers.add_parser("litnet-preview")
    litnet.add_argument("--output", type=Path, required=True)
    litnet.add_argument("--claim-audit", type=Path, required=True)
    litnet.add_argument("--litnet-work", default="")
    litnet.add_argument("--zotero-record", default="")
    litnet.set_defaults(func=litnet_preview_command)
    return parser


def main() -> int:
    args = make_parser().parse_args()
    try:
        return args.func(args)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
