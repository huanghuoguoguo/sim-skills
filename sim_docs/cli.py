"""CLI entry point for sim-docs unified document service."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .service import DocumentService
from .check_engine import CHECK_SCHEMA


def cmd_parse(args) -> int:
    """Handle parse subcommand."""
    service = DocumentService()
    facts = service.parse(args.input)

    output_data = facts.to_dict()
    _write_output(output_data, args.output)
    return 0


def cmd_query_style(args) -> int:
    """Handle query-style subcommand."""
    service = DocumentService()
    results = service.query_style(args.input, args.style)

    if not results:
        print(json.dumps({"error": f"Style containing '{args.style}' not found"}), file=sys.stderr)
        return 1

    output_data = [
        {
            "name": s.name,
            "style_id": s.style_id,
            "type": s.style_type,
            "properties": s.properties,
        }
        for s in results
    ]
    _write_output(output_data, args.output)
    return 0


def cmd_query_text(args) -> int:
    """Handle query-text subcommand."""
    service = DocumentService()
    results = service.query_text(args.input, args.keyword)

    output_data = [
        {
            "id": p.id,
            "index": p.index,
            "text": p.text,
            "style_name": p.style_name,
            "properties": p.properties,
        }
        for p in results
    ]
    _write_output(output_data, args.output)
    return 0


def cmd_check(args) -> int:
    """Handle check subcommand."""
    service = DocumentService()

    if args.schema:
        _write_output(CHECK_SCHEMA, None)
        return 0

    checks_path = Path(args.checks).expanduser().resolve()
    checks_raw = json.loads(checks_path.read_text(encoding="utf-8"))
    checks = checks_raw.get("checks", checks_raw) if isinstance(checks_raw, dict) else checks_raw

    result = service.batch_check(args.input, checks)
    _write_output(result, args.output)
    return 0


def cmd_stats(args) -> int:
    """Handle stats subcommand."""
    service = DocumentService()

    result = service.stats(
        args.input,
        style_hint=args.style_hint,
        min_length=args.min_length,
        require_body_shape=args.require_body_shape,
        exclude_texts=args.exclude_text,
        heading_prefixes=args.heading_prefix,
        heading_keywords=args.heading_keyword,
        instruction_hints=args.instruction_hint,
        sample_limit=args.sample_limit,
    )

    output_data = {
        "input": args.input,
        "filters": result.get("filters", {}),
        "summary": result.get("summary", {}),
    }
    _write_output(output_data, args.output)
    return 0


def cmd_render(args) -> int:
    """Handle render subcommand."""
    service = DocumentService()

    result = service.render(args.input, page=args.page, output=args.output)
    if args.output:
        print(f"Rendered page {args.page} to '{args.output}'")
    return 0


def cmd_validate(args) -> int:
    """Handle validate subcommand."""
    service = DocumentService()

    result = service.validate(args.input, auto_repair=args.auto_repair, verbose=args.verbose)

    if result["success"]:
        print("All validations PASSED!")
        if result["repairs"]:
            print(f"Auto-repaired {result['repairs']} issue(s)")
        return 0
    else:
        print("Validation FAILED", file=sys.stderr)
        return 1


def cmd_inspect(args) -> int:
    """Handle inspect subcommand."""
    service = DocumentService()

    result = service.inspect(
        args.input,
        output_dir=args.output_dir,
        show=args.show,
        list_files=args.list,
        merge_runs=args.merge_runs,
    )

    print(result["message"])
    print(f"Output: {result['output_dir']}")

    if result.get("files"):
        print("\nXML files:")
        for f in result["files"]:
            print(f"  {f['path']} ({f['size']} bytes)")

    if result.get("show_content"):
        print(f"\n--- {args.show} ---")
        print(result["show_content"])
    elif result.get("show_error"):
        print(f"\n{result['show_error']}")

    return 0


def cmd_read_text(args) -> int:
    """Handle read-text subcommand."""
    service = DocumentService()
    result = service.read_text(args.input)
    _write_output(result, args.output)
    return 0


def cmd_read_pdf(args) -> int:
    """Handle read-pdf subcommand."""
    service = DocumentService()
    result = service.read_pdf(
        args.input,
        pages=args.pages,
        extract_tables=args.tables,
        extract_all=args.all,
    )
    _write_output(result, args.output)
    return 0


def cmd_compare(args) -> int:
    """Handle compare subcommand."""
    service = DocumentService()
    result = service.compare_docs(args.reference, args.target)
    _write_output(result, args.output)

    if args.report:
        # Generate markdown report
        report = _generate_diff_report(result["diffs"], args.reference, args.target)
        Path(args.report).write_text(report, encoding="utf-8")
        print(f"Markdown report saved to: {args.report}", file=sys.stderr)

    return 0


def cmd_spec_check(args) -> int:
    """Handle spec-check subcommand."""
    service = DocumentService()

    if args.mode == "conflicts":
        result = service.spec_check_conflicts(args.input)
        _write_output(result, args.output)
        return 0 if result["status"] == "pass" else 1

    elif args.mode == "structure":
        result = service.spec_check_structure(args.input)
        _write_output(result, args.output)
        return 0 if result["status"] == "pass" else 1

    elif args.mode == "body-consistency":
        # Load evidence JSON
        evidence_path = Path(args.evidence).expanduser().resolve()
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

        # Load checks JSON
        checks_path = Path(args.checks).expanduser().resolve()
        checks_raw = json.loads(checks_path.read_text(encoding="utf-8"))
        checks = checks_raw.get("checks", checks_raw) if isinstance(checks_raw, dict) else checks_raw

        result = service.spec_check_body_consistency(evidence, checks)
        _write_output(result, args.output)
        return 0 if result["status"] == "pass" else 1

    else:
        print(f"Unknown mode: {args.mode}", file=sys.stderr)
        return 1


def _write_output(data, output_path: str | None) -> None:
    """Write JSON data to file or stdout."""
    content = json.dumps(data, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
        sys.stdout.write("\n")


def _generate_diff_report(diffs: list, ref_path: str, target_path: str) -> str:
    """Generate Markdown report for document comparison."""
    from datetime import datetime

    lines = [
        "# 文档格式比对报告",
        "",
        f"**参考文档**: {Path(ref_path).name}",
        f"**目标文档**: {Path(target_path).name}",
        f"**比对时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总计",
        "",
        f"共发现 **{len(diffs)}** 处差异。",
        "",
    ]

    by_type = {"structure": [], "layout": [], "style": [], "other": []}
    for diff in diffs:
        by_type.get(diff.get("type", "other"), by_type["other"]).append(diff)

    if by_type["structure"]:
        lines.append("## 结构差异")
        lines.append("")
        for i, diff in enumerate(by_type["structure"], 1):
            lines.append(f"{i}. {diff['message']}")
            lines.append("")

    if by_type["layout"]:
        lines.append("## 布局差异")
        lines.append("")
        for i, diff in enumerate(by_type["layout"], 1):
            lines.append(f"{i}. {diff['message']}")
            lines.append("")

    if not diffs:
        lines.append("两份文档格式一致。")

    return "\n".join(lines)


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="sim-docs",
        description="Unified document service for parsing, querying, checking, and rendering documents.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # parse subcommand
    parse_parser = subparsers.add_parser("parse", help="Parse Word document to structured facts")
    parse_parser.add_argument("input", help="Path to .docx/.dotm file")
    parse_parser.add_argument("--output", help="Output JSON file path")

    # query-style subcommand
    query_style_parser = subparsers.add_parser("query-style", help="Query document style properties")
    query_style_parser.add_argument("input", help="Path to .docx/.dotm file")
    query_style_parser.add_argument("--style", required=True, help="Style name to query")
    query_style_parser.add_argument("--output", help="Output JSON file path")

    # query-text subcommand
    query_text_parser = subparsers.add_parser("query-text", help="Query paragraphs by keyword")
    query_text_parser.add_argument("input", help="Path to .docx/.dotm file")
    query_text_parser.add_argument("--keyword", required=True, help="Keyword to search")
    query_text_parser.add_argument("--output", help="Output JSON file path")

    # check subcommand
    check_parser = subparsers.add_parser("check", help="Batch check document properties")
    check_parser.add_argument("input", nargs="?", help="Path to .docx/.dotm file")
    check_parser.add_argument("checks", nargs="?", help="Path to checks JSON file")
    check_parser.add_argument("--output", help="Output JSON file path")
    check_parser.add_argument("--schema", action="store_true", help="Print supported check types")

    # stats subcommand
    stats_parser = subparsers.add_parser("stats", help="Paragraph filtering and statistics")
    stats_parser.add_argument("input", help="Path to .docx/.dotm file")
    stats_parser.add_argument("--output", help="Output JSON file path")
    stats_parser.add_argument("--style-hint", help="Style name to filter")
    stats_parser.add_argument("--min-length", type=int, default=0, help="Min paragraph text length")
    stats_parser.add_argument("--require-body-shape", action="store_true", help="Only paragraphs with justify/indent")
    stats_parser.add_argument("--exclude-text", action="append", default=[], help="Exclude paragraphs containing text")
    stats_parser.add_argument("--heading-prefix", action="append", default=[], help="Regex for heading exclusion")
    stats_parser.add_argument("--heading-keyword", action="append", default=[], help="Keyword prefix for heading exclusion")
    stats_parser.add_argument("--instruction-hint", action="append", default=[], help="Text hint for instruction exclusion")
    stats_parser.add_argument("--sample-limit", type=int, default=8, help="Max candidate examples")

    # render subcommand
    render_parser = subparsers.add_parser("render", help="Render page to image")
    render_parser.add_argument("input", help="Path to .docx/.dotm file")
    render_parser.add_argument("--page", type=int, default=1, help="Page number (1-indexed)")
    render_parser.add_argument("--output", required=True, help="Output image file (e.g., page1.png)")

    # validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate document XML structure")
    validate_parser.add_argument("input", help="Path to .docx file")
    validate_parser.add_argument("--auto-repair", action="store_true", help="Automatically repair issues")
    validate_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # inspect subcommand
    inspect_parser = subparsers.add_parser("inspect", help="Unpack document for XML inspection")
    inspect_parser.add_argument("input", help="Path to .docx/.dotm file")
    inspect_parser.add_argument("--output-dir", help="Output directory for unpacked files")
    inspect_parser.add_argument("--show", help="Show content of specific XML file")
    inspect_parser.add_argument("--list", action="store_true", help="List all XML files")
    inspect_parser.add_argument("--merge-runs", type=lambda x: x.lower() == "true", default=True, help="Merge adjacent runs")

    # read-text subcommand
    read_text_parser = subparsers.add_parser("read-text", help="Read text from .txt/.md/.docx")
    read_text_parser.add_argument("input", help="Path to text file")
    read_text_parser.add_argument("--output", help="Output JSON file path")

    # read-pdf subcommand
    read_pdf_parser = subparsers.add_parser("read-pdf", help="Extract content from PDF")
    read_pdf_parser.add_argument("input", help="Path to PDF file")
    read_pdf_parser.add_argument("--pages", help="Page range (e.g., '1-5')")
    read_pdf_parser.add_argument("--tables", action="store_true", help="Extract tables only")
    read_pdf_parser.add_argument("--all", action="store_true", help="Full extraction (text + tables)")
    read_pdf_parser.add_argument("--output", help="Output JSON file path")

    # compare subcommand
    compare_parser = subparsers.add_parser("compare", help="Compare two documents")
    compare_parser.add_argument("reference", help="Path to reference .docx file")
    compare_parser.add_argument("target", help="Path to target .docx file")
    compare_parser.add_argument("--output", help="Output JSON file path")
    compare_parser.add_argument("--report", help="Output Markdown report path")

    # spec-check subcommand
    spec_check_parser = subparsers.add_parser("spec-check", help="Evaluate spec.md quality")
    spec_check_parser.add_argument("--mode", required=True, choices=["conflicts", "structure", "body-consistency"],
                                   help="Check mode: conflicts, structure, or body-consistency")
    spec_check_parser.add_argument("input", nargs="?", help="Path to spec.md file (for conflicts/structure mode)")
    spec_check_parser.add_argument("--evidence", help="Path to evidence JSON (for body-consistency mode)")
    spec_check_parser.add_argument("--checks", help="Path to checks JSON (for body-consistency mode)")
    spec_check_parser.add_argument("--output", help="Output JSON file path")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    # Dispatch to subcommand handler
    handlers = {
        "parse": cmd_parse,
        "query-style": cmd_query_style,
        "query-text": cmd_query_text,
        "check": cmd_check,
        "stats": cmd_stats,
        "render": cmd_render,
        "validate": cmd_validate,
        "inspect": cmd_inspect,
        "read-text": cmd_read_text,
        "read-pdf": cmd_read_pdf,
        "compare": cmd_compare,
        "spec-check": cmd_spec_check,
    }

    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())