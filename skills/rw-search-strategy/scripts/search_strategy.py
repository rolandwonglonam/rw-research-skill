#!/usr/bin/env python3
"""Render and verify multi-database literature search strategies."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


VERIFIED_STATUSES = {
    "verified_by_public_api",
    "verified_in_subscribed_platform",
    "user_confirmed",
}
VOCABULARIES = ("mesh", "emtree", "cinahl", "apa")
VOCABULARY_SET = set(VOCABULARIES)
PLATFORMS = {
    "pubmed",
    "ovid_medline",
    "embase_com",
    "ovid_embase",
    "ebsco_cinahl",
    "ebsco_psycinfo",
    "ovid_psycinfo",
    "proquest_psycinfo",
}
PLATFORM_VOCABULARY = {
    "pubmed": "mesh",
    "ovid_medline": "mesh",
    "embase_com": "emtree",
    "ovid_embase": "emtree",
    "ebsco_cinahl": "cinahl",
    "ebsco_psycinfo": "apa",
    "ovid_psycinfo": "apa",
    "proquest_psycinfo": "apa",
}


def load_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dump_json(value: Any, output: str | None = None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def http_json(url: str, timeout: int = 30) -> Any:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "rw-search-strategy/0.10"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def normalize_heading(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        return {"label": value, "status": "candidate", "explode": True, "focus": False}
    row = dict(value)
    row.setdefault("status", "candidate")
    row.setdefault("explode", True)
    row.setdefault("focus", False)
    return row


def quote_double(value: str) -> str:
    return value.replace('"', '\\"')


def quote_single(value: str) -> str:
    return value.replace("'", "''")


def ovid_term(value: str) -> str:
    return f'"{quote_double(value)}"' if " " in value else value


def free_terms(concept: dict[str, Any]) -> list[str]:
    rows: list[str] = []
    for value in concept.get("free_text", []):
        term = value.get("term", "") if isinstance(value, dict) else str(value)
        term = term.strip()
        if term and term not in rows:
            rows.append(term)
    return rows


def eligible_headings(concept: dict[str, Any], vocabulary: str, include_candidates: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for value in concept.get("headings", {}).get(vocabulary, []):
        row = normalize_heading(value)
        if row["status"] in VERIFIED_STATUSES or include_candidates:
            selected.append(row)
        else:
            excluded.append(row)
    return selected, excluded


def render_controlled(platform: str, row: dict[str, Any]) -> str:
    label = str(row["label"]).strip()
    explode = bool(row.get("explode", True))
    focus = bool(row.get("focus", False))
    if platform == "pubmed":
        field = "Majr" if focus else "Mesh"
        return f'"{quote_double(label)}"[{field}:noexp]' if not explode else f'"{quote_double(label)}"[{field}]'
    if platform in {"ovid_medline", "ovid_embase", "ovid_psycinfo"}:
        prefix = "*" if focus else ""
        return f"exp {prefix}{ovid_term(label)}/" if explode else f"{prefix}{ovid_term(label)}/"
    if platform == "embase_com":
        suffix = "/exp/mj" if focus and explode else "/mj" if focus else "/exp" if explode else "/de"
        return f"'{quote_single(label)}'{suffix}"
    if platform == "ebsco_cinahl":
        field = "MM" if focus else "MH"
        plus = "+" if explode else ""
        return f'{field} "{quote_double(label)}{plus}"'
    if platform == "ebsco_psycinfo":
        return f'DE "{quote_double(label)}"'
    if platform == "proquest_psycinfo":
        operator = "MAINSUBJECT.EXACT.EXPLODE" if explode else "MAINSUBJECT.EXACT"
        return f'{operator}("{quote_double(label)}")'
    raise ValueError(f"unsupported platform: {platform}")


def render_free(platform: str, term: str) -> str:
    if platform == "pubmed":
        return f'"{quote_double(term)}"[tiab]' if " " in term and "*" not in term else f"{term}[tiab]"
    if platform in {"ovid_medline", "ovid_embase"}:
        return f"{ovid_term(term)}.ti,ab,kf."
    if platform == "ovid_psycinfo":
        return f"{ovid_term(term)}.ti,ab,id."
    if platform == "embase_com":
        return f"'{quote_single(term)}':ti,ab,kw"
    if platform in {"ebsco_cinahl", "ebsco_psycinfo"}:
        escaped = quote_double(term)
        return f'(TI "{escaped}" OR AB "{escaped}")'
    if platform == "proquest_psycinfo":
        return f'TI,AB("{quote_double(term)}")'
    raise ValueError(f"unsupported platform: {platform}")


def render_platform(strategy: dict[str, Any], platform: str, include_candidates: bool = False) -> dict[str, Any]:
    if platform not in PLATFORMS:
        raise ValueError(f"unsupported platform: {platform}")
    vocabulary = PLATFORM_VOCABULARY[platform]
    blocks: list[dict[str, Any]] = []
    excluded_candidates: list[dict[str, Any]] = []
    for concept in strategy.get("concepts", []):
        headings, excluded = eligible_headings(concept, vocabulary, include_candidates)
        controlled = [render_controlled(platform, row) for row in headings]
        free = [render_free(platform, term) for term in free_terms(concept)]
        clauses = controlled + free
        if not clauses:
            continue
        blocks.append(
            {
                "concept_id": concept.get("id"),
                "label": concept.get("label"),
                "controlled_count": len(controlled),
                "free_text_count": len(free),
                "query": "(" + " OR ".join(clauses) + ")",
            }
        )
        for row in excluded:
            excluded_candidates.append(
                {
                    "concept_id": concept.get("id"),
                    "vocabulary": vocabulary,
                    "label": row.get("label"),
                    "status": row.get("status"),
                }
            )
    return {
        "platform": platform,
        "vocabulary": vocabulary,
        "query": " AND ".join(block["query"] for block in blocks),
        "concept_blocks": blocks,
        "excluded_unverified_headings": excluded_candidates,
        "requires_platform_validation": vocabulary != "mesh" and bool(excluded_candidates),
    }


def heading_audit(strategy: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for concept in strategy.get("concepts", []):
        for vocabulary in VOCABULARIES:
            for value in concept.get("headings", {}).get(vocabulary, []):
                row = normalize_heading(value)
                rows.append(
                    {
                        "concept_id": concept.get("id"),
                        "concept_label": concept.get("label"),
                        "vocabulary": vocabulary,
                        "label": row.get("label"),
                        "identifier": row.get("identifier"),
                        "status": row.get("status"),
                        "verified": row.get("status") in VERIFIED_STATUSES,
                        "source": row.get("source"),
                        "verified_at": row.get("verified_at"),
                        "explode": row.get("explode"),
                        "focus": row.get("focus"),
                    }
                )
    return rows


def validate_strategy(strategy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not strategy.get("question"):
        errors.append("question is required")
    concepts = strategy.get("concepts", [])
    if not concepts:
        errors.append("at least one concept is required")
    seen: set[str] = set()
    for index, concept in enumerate(concepts, 1):
        concept_id = str(concept.get("id", "")).strip()
        if not concept_id:
            errors.append(f"concept {index} has no id")
        elif concept_id in seen:
            errors.append(f"duplicate concept id: {concept_id}")
        seen.add(concept_id)
        for vocabulary, values in concept.get("headings", {}).items():
            if vocabulary not in VOCABULARY_SET:
                errors.append(f"unsupported vocabulary: {vocabulary}")
            for value in values:
                row = normalize_heading(value)
                if not row.get("label"):
                    errors.append(f"{concept_id}/{vocabulary} heading has no label")
                if vocabulary != "mesh" and row.get("status") == "verified_by_public_api":
                    errors.append(f"{concept_id}/{vocabulary} cannot use verified_by_public_api")
    return errors


def render_strategy(strategy: dict[str, Any], targets: list[str] | None, include_candidates: bool) -> dict[str, Any]:
    errors = validate_strategy(strategy)
    if errors:
        raise ValueError("; ".join(errors))
    selected_targets = targets or strategy.get("targets") or sorted(PLATFORMS)
    unknown = set(selected_targets) - PLATFORMS
    if unknown:
        raise ValueError("unsupported targets: " + ", ".join(sorted(unknown)))
    return {
        "schema_version": "1.0",
        "question": strategy["question"],
        "language": strategy.get("language", "unspecified"),
        "framework": strategy.get("framework", "open"),
        "generated_at": now_utc(),
        "include_candidates": include_candidates,
        "heading_audit": heading_audit(strategy),
        "platforms": [
            render_platform(strategy, platform, include_candidates)
            for platform in selected_targets
        ],
        "status_note": (
            "Candidate headings were rendered and still require platform validation."
            if include_candidates
            else "Unverified headings were excluded from executable queries."
        ),
    }


def markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Search strategy",
        "",
        f"- Question: {result['question']}",
        f"- Language: {result['language']}",
        f"- Framework: {result['framework']}",
        f"- Generated: {result['generated_at']}",
        "",
        "## Platform queries",
        "",
    ]
    for row in result["platforms"]:
        lines += [
            f"### {row['platform']}",
            "",
            "```text",
            row["query"] or "[no executable terms]",
            "```",
            "",
        ]
        if row["excluded_unverified_headings"]:
            labels = ", ".join(item["label"] for item in row["excluded_unverified_headings"])
            lines += [f"- Excluded unverified headings: {labels}", ""]
    lines += ["## Controlled vocabulary audit", "", "| Concept | Vocabulary | Heading | Status | Source |", "|---|---|---|---|---|"]
    for row in result["heading_audit"]:
        lines.append(
            f"| {row['concept_id']} | {row['vocabulary']} | {row['label']} | {row['status']} | {row['source'] or ''} |"
        )
    return "\n".join(lines) + "\n"


def mesh_lookup(label: str, match: str, limit: int, year: str, timeout: int) -> dict[str, Any]:
    params = urlencode({"label": label, "match": match, "limit": limit, "year": year})
    matches = http_json(f"https://id.nlm.nih.gov/mesh/lookup/descriptor?{params}", timeout)
    output: list[dict[str, Any]] = []
    for match_row in matches:
        resource = str(match_row.get("resource", ""))
        descriptor_id = resource.rstrip("/").rsplit("/", 1)[-1]
        detail_params = urlencode({"descriptor": descriptor_id, "includes": "terms,qualifiers,seealso"})
        details = http_json(f"https://id.nlm.nih.gov/mesh/lookup/details?{detail_params}", timeout)
        resource_url = (
            f"https://id.nlm.nih.gov/mesh/{descriptor_id}.json"
            if year == "current"
            else f"https://id.nlm.nih.gov/mesh/{year}/{descriptor_id}.json"
        )
        resource_data = http_json(resource_url, timeout)
        graph = resource_data.get("@graph", []) if isinstance(resource_data, dict) else resource_data
        if isinstance(resource_data, dict) and not graph:
            graph = [resource_data]
        descriptor = next(
            (node for node in graph if str(node.get("@id", "")).endswith(descriptor_id)),
            graph[0] if graph else {},
        )
        tree_numbers = descriptor.get("treeNumber", [])
        if isinstance(tree_numbers, str):
            tree_numbers = [tree_numbers]
        output.append(
            {
                "label": match_row.get("label"),
                "identifier": descriptor_id,
                "resource": resource,
                "tree_numbers": [str(value).rstrip("/").rsplit("/", 1)[-1] for value in tree_numbers],
                "active": descriptor.get(
                    "active",
                    descriptor.get("http://id.nlm.nih.gov/mesh/vocab#active"),
                ),
                "date_introduced": descriptor.get("dateIntroduced"),
                "last_updated": descriptor.get("lastUpdated"),
                "annotation": mesh_literal(descriptor.get("annotation")),
                "details": details,
                "details_year": "current",
                "status": "verified_by_public_api",
                "source": "NLM MeSH RDF API",
                "verified_at": now_utc(),
                "year": year,
            }
        )
    return {"query": label, "match": match, "year": year, "results": output}


def pubmed_check(query: str, timeout: int) -> dict[str, Any]:
    params = urlencode({"db": "pubmed", "term": query, "retmode": "json", "retmax": 0, "usehistory": "n"})
    data = http_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}", timeout)
    result = data.get("esearchresult", {})
    return {
        "query": query,
        "count": int(result.get("count", 0)),
        "query_translation": result.get("querytranslation"),
        "warning_list": result.get("warninglist", {}),
        "checked_at": now_utc(),
        "source": "NCBI PubMed ESearch",
    }


def mesh_literal(value: Any) -> Any:
    if isinstance(value, dict) and "@value" in value:
        return value["@value"]
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="Render database-specific strategies.")
    render.add_argument("--input", required=True)
    render.add_argument("--output")
    render.add_argument("--target", action="append", choices=sorted(PLATFORMS))
    render.add_argument("--include-candidates", action="store_true")
    render.add_argument("--format", choices=["json", "markdown"], default="json")

    mesh = sub.add_parser("mesh-lookup", help="Verify descriptors with the NLM MeSH RDF API.")
    mesh.add_argument("--label", required=True)
    mesh.add_argument("--match", choices=["exact", "contains", "startswith"], default="contains")
    mesh.add_argument("--limit", type=int, default=10)
    mesh.add_argument("--year", default="current")
    mesh.add_argument("--timeout", type=int, default=30)
    mesh.add_argument("--output")

    pubmed = sub.add_parser("pubmed-check", help="Check a PubMed query with NCBI ESearch.")
    pubmed.add_argument("--query", required=True)
    pubmed.add_argument("--timeout", type=int, default=30)
    pubmed.add_argument("--output")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "render":
            result = render_strategy(load_json(args.input), args.target, args.include_candidates)
            if args.format == "markdown":
                text = markdown_report(result)
                if args.output:
                    Path(args.output).write_text(text, encoding="utf-8")
                else:
                    sys.stdout.write(text)
            else:
                dump_json(result, args.output)
        elif args.command == "mesh-lookup":
            dump_json(mesh_lookup(args.label, args.match, args.limit, args.year, args.timeout), args.output)
        elif args.command == "pubmed-check":
            dump_json(pubmed_check(args.query, args.timeout), args.output)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.stderr.write(json.dumps({"error": str(exc)}, ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
