"""Inspect engine for unpacking and examining Word document XML.

Migrated from .claude/skills/inspect-word-xml/scripts/run.py.
"""

from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Any

import defusedxml.minidom


SMART_QUOTE_REPLACEMENTS = {
    "\u201c": "&#x201C;",
    "\u201d": "&#x201D;",
    "\u2018": "&#x2018;",
    "\u2019": "&#x2019;",
}


def unpack(input_file: str | Path, output_directory: str | Path, merge_runs: bool = True) -> str:
    """Unpack a .docx/.dotm to a directory with pretty-printed XML.

    Args:
        input_file: Path to .docx or .dotm file.
        output_directory: Output directory for unpacked files.
        merge_runs: Merge adjacent runs with identical formatting.

    Returns:
        Status message string.
    """
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
    """Pretty-print XML file."""
    try:
        content = xml_file.read_text(encoding="utf-8")
        dom = defusedxml.minidom.parseString(content)
        xml_file.write_bytes(dom.toprettyxml(indent="  ", encoding="utf-8"))
    except Exception:
        pass


def _escape_smart_quotes(xml_file: Path) -> None:
    """Escape smart quotes in XML file."""
    try:
        content = xml_file.read_text(encoding="utf-8")
        for char, entity in SMART_QUOTE_REPLACEMENTS.items():
            content = content.replace(char, entity)
        xml_file.write_text(content, encoding="utf-8")
    except Exception:
        pass


def _merge_runs_in_document(output_path: Path) -> int:
    """Merge adjacent runs with identical formatting."""
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


def _find_elements(root: Any, tag: str) -> list:
    """Find all elements with given tag."""
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


def _get_child(parent: Any, tag: str) -> Any | None:
    """Get child element with given tag."""
    for child in parent.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            name = child.localName or child.tagName
            if name == tag or name.endswith(f":{tag}"):
                return child
    return None


def _is_run(node: Any) -> bool:
    """Check if node is a run element."""
    name = node.localName or node.tagName
    return name == "r" or name.endswith(":r")


def _merge_runs_in_container(container: Any) -> int:
    """Merge runs in a container element."""
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


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def inspect_document(
    input_file: str | Path,
    output_dir: str | None = None,
    show: str | None = None,
    list_files: bool = False,
    merge_runs: bool = True,
) -> dict:
    """Unpack Word document for XML inspection.

    Args:
        input_file: Path to .docx or .dotm file.
        output_dir: Output directory for unpacked files.
        show: Show content of a specific XML file.
        list_files: List all XML files in the document.
        merge_runs: Merge adjacent runs with identical formatting.

    Returns:
        Dict with message, output_dir, and optionally files/content.

    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If file type is not supported.
    """
    input_path = Path(input_file)

    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_file}")

    if input_path.suffix.lower() not in {".docx", ".dotm"}:
        raise ValueError(f"File must be .docx or .dotm: {input_file}")

    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="inspect_")

    message = unpack(input_path, output_dir, merge_runs=merge_runs)

    if "Error" in message:
        raise ValueError(message)

    result = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "message": message,
    }

    output_path = Path(output_dir)

    if list_files:
        xml_files = sorted(output_path.rglob("*.xml"))
        rels_files = sorted(output_path.rglob("*.rels"))
        result["files"] = [
            {"path": str(f.relative_to(output_path)), "size": f.stat().st_size}
            for f in xml_files + rels_files
        ]

    if show:
        show_path = output_path / show
        if show_path.exists():
            result["show_content"] = show_path.read_text(encoding="utf-8")
        else:
            result["show_error"] = f"File not found: {show}"

    return result