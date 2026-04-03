#!/usr/bin/env python3
"""Unpack a Word document for raw XML inspection.

Usage:
    python run.py <file.docx> [--output-dir DIR] [--show PATH] [--list] [--merge-runs true|false]

Adapted from Anthropic's official docx skill (unpack.py).
"""

import argparse
import json
import sys
import tempfile
import zipfile
from pathlib import Path

import defusedxml.minidom

# Resolve shared libs
libs_path = Path(__file__).parent.parent.parent / "__libs__"
if str(libs_path) not in sys.path:
    sys.path.insert(0, str(libs_path))

from utils import resolve_path


SMART_QUOTE_REPLACEMENTS = {
    "\u201c": "&#x201C;",
    "\u201d": "&#x201D;",
    "\u2018": "&#x2018;",
    "\u2019": "&#x2019;",
}


def unpack(input_file: str, output_directory: str, merge_runs: bool = True) -> str:
    """Unpack a .docx/.dotm to a directory with pretty-printed XML."""
    input_path = Path(input_file)
    output_path = Path(output_directory)

    if not input_path.exists():
        return f"Error: {input_file} does not exist"

    if input_path.suffix.lower() not in {".docx", ".dotm"}:
        return f"Error: {input_file} must be a .docx or .dotm file"

    try:
        output_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(input_path, "r") as zf:
            zf.extractall(output_path)

        xml_files = list(output_path.rglob("*.xml")) + list(output_path.rglob("*.rels"))
        for xml_file in xml_files:
            _pretty_print_xml(xml_file)

        message = f"Unpacked {input_file} ({len(xml_files)} XML files)"

        if merge_runs:
            merge_count = _merge_runs_in_document(output_path)
            if merge_count > 0:
                message += f", merged {merge_count} runs"

        for xml_file in xml_files:
            _escape_smart_quotes(xml_file)

        return message

    except zipfile.BadZipFile:
        return f"Error: {input_file} is not a valid Office file"
    except Exception as e:
        return f"Error unpacking: {e}"


def _pretty_print_xml(xml_file: Path) -> None:
    try:
        content = xml_file.read_text(encoding="utf-8")
        dom = defusedxml.minidom.parseString(content)
        xml_file.write_bytes(dom.toprettyxml(indent="  ", encoding="utf-8"))
    except Exception:
        pass


def _escape_smart_quotes(xml_file: Path) -> None:
    try:
        content = xml_file.read_text(encoding="utf-8")
        for char, entity in SMART_QUOTE_REPLACEMENTS.items():
            content = content.replace(char, entity)
        xml_file.write_text(content, encoding="utf-8")
    except Exception:
        pass


def _merge_runs_in_document(output_path: Path) -> int:
    """Simple run merging: merge adjacent <w:r> with identical <w:rPr>."""
    doc_xml = output_path / "word" / "document.xml"
    if not doc_xml.exists():
        return 0

    try:
        dom = defusedxml.minidom.parseString(doc_xml.read_text(encoding="utf-8"))
        root = dom.documentElement

        # Remove proofErr elements that block merging
        for elem in _find_elements(root, "proofErr"):
            if elem.parentNode:
                elem.parentNode.removeChild(elem)

        # Strip rsid attributes from runs
        for run in _find_elements(root, "r"):
            for attr in list(run.attributes.values()):
                if "rsid" in attr.name.lower():
                    run.removeAttribute(attr.name)

        # Merge runs in each container
        containers = {run.parentNode for run in _find_elements(root, "r")}
        merge_count = 0
        for container in containers:
            merge_count += _merge_runs_in_container(container)

        doc_xml.write_bytes(dom.toxml(encoding="UTF-8"))
        return merge_count

    except Exception:
        return 0


def _find_elements(root, tag: str) -> list:
    results = []
    def traverse(node):
        if node.nodeType == node.ELEMENT_NODE:
            name = node.localName or node.tagName
            if name == tag or name.endswith(f":{tag}"):
                results.append(node)
            for child in node.childNodes:
                traverse(child)
    traverse(root)
    return results


def _get_child(parent, tag: str):
    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            name = child.localName or child.tagName
            if name == tag or name.endswith(f":{tag}"):
                return child
    return None


def _is_run(node) -> bool:
    name = node.localName or node.tagName
    return name == "r" or name.endswith(":r")


def _merge_runs_in_container(container) -> int:
    merge_count = 0
    runs = [c for c in container.childNodes
            if c.nodeType == c.ELEMENT_NODE and _is_run(c)]

    i = 0
    while i < len(runs) - 1:
        curr, next_r = runs[i], runs[i + 1]
        rpr1 = _get_child(curr, "rPr")
        rpr2 = _get_child(next_r, "rPr")

        can_merge = False
        if rpr1 is None and rpr2 is None:
            can_merge = True
        elif rpr1 is not None and rpr2 is not None:
            can_merge = rpr1.toxml() == rpr2.toxml()

        if can_merge:
            # Move content (non-rPr) from next to current
            for child in list(next_r.childNodes):
                if child.nodeType == child.ELEMENT_NODE:
                    name = child.localName or child.tagName
                    if name != "rPr" and not name.endswith(":rPr"):
                        curr.appendChild(child)
            container.removeChild(next_r)
            runs.pop(i + 1)
            merge_count += 1
        else:
            i += 1

    return merge_count


def main():
    parser = argparse.ArgumentParser(description="Unpack Word document for XML inspection")
    parser.add_argument("file", help="Path to .docx or .dotm file")
    parser.add_argument("--output-dir", help="Output directory for unpacked files")
    parser.add_argument("--show", help="Show content of a specific XML file (e.g., word/document.xml)")
    parser.add_argument("--list", action="store_true", help="List all XML files in the document")
    parser.add_argument(
        "--merge-runs",
        type=lambda x: x.lower() == "true",
        default=True,
        metavar="true|false",
        help="Merge adjacent runs with identical formatting (default: true)",
    )
    args = parser.parse_args()

    file_path = resolve_path(args.file)
    if not Path(file_path).exists():
        print(f"Error: File not found: {args.file}")
        sys.exit(1)

    # Determine output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = tempfile.mkdtemp(prefix="inspect_")

    # Unpack
    message = unpack(file_path, output_dir, merge_runs=args.merge_runs)
    if "Error" in message:
        print(message)
        sys.exit(1)

    print(message)
    print(f"Output: {output_dir}")

    output_path = Path(output_dir)

    if args.list:
        print("\nXML files:")
        for f in sorted(output_path.rglob("*.xml")):
            rel = f.relative_to(output_path)
            size = f.stat().st_size
            print(f"  {rel} ({size} bytes)")
        for f in sorted(output_path.rglob("*.rels")):
            rel = f.relative_to(output_path)
            size = f.stat().st_size
            print(f"  {rel} ({size} bytes)")

    if args.show:
        show_path = output_path / args.show
        if show_path.exists():
            print(f"\n--- {args.show} ---")
            print(show_path.read_text(encoding="utf-8"))
        else:
            print(f"\nFile not found: {args.show}")
            print("Available files:")
            for f in sorted(output_path.rglob("*.xml")):
                print(f"  {f.relative_to(output_path)}")


if __name__ == "__main__":
    main()
