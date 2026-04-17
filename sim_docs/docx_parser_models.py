from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Any


def to_plain_data(value: Any) -> Any:
    if is_dataclass(value):
        return {
            key: to_plain_data(item)
            for key, item in asdict(value).items()
        }
    if isinstance(value, dict):
        return {key: to_plain_data(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain_data(item) for item in value]
    return value


@dataclass
class ParagraphFact:
    id: str
    index: int
    text: str
    style_name: str | None
    style_id: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)
    property_sources: dict[str, str] = field(default_factory=dict)
    numbering: dict[str, Any] | None = None


@dataclass
class StyleFact:
    name: str
    style_id: str | None
    style_type: str | None
    base_style: str | None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class HeaderFooterFact:
    type: str  # "header" or "footer"
    section_index: int
    paragraphs: list[dict]  # List of paragraph facts
    text: str = ""  # Combined text
    linked_to_previous: bool = False


@dataclass
class WordDocumentFacts:
    format: str
    metadata: dict[str, Any]
    layout: dict[str, Any]
    paragraphs: list[ParagraphFact]
    styles: list[StyleFact]
    headers: list[HeaderFooterFact] = field(default_factory=list)
    footers: list[HeaderFooterFact] = field(default_factory=list)
    tables: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return to_plain_data(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WordDocumentFacts":
        """Load facts from a dictionary (e.g., parsed from JSON)."""
        paragraphs = [
            ParagraphFact(
                id=p.get("id", f"p-{i}"),
                index=p.get("index", i),
                text=p.get("text", ""),
                style_name=p.get("style_name"),
                style_id=p.get("style_id"),
                properties=p.get("properties", {}),
                property_sources=p.get("property_sources", {}),
                numbering=p.get("numbering"),
            )
            for i, p in enumerate(data.get("paragraphs", []))
        ]

        styles = [
            StyleFact(
                name=s.get("name", ""),
                style_id=s.get("style_id"),
                style_type=s.get("type"),
                base_style=s.get("base_style"),
                properties=s.get("properties", {}),
            )
            for s in data.get("styles", [])
        ]

        headers = [
            HeaderFooterFact(
                type=h.get("type", "header"),
                section_index=h.get("section_index", 0),
                paragraphs=h.get("paragraphs", []),
                text=h.get("text", ""),
                linked_to_previous=h.get("linked_to_previous", False),
            )
            for h in data.get("headers", [])
        ]

        footers = [
            HeaderFooterFact(
                type=f.get("type", "footer"),
                section_index=f.get("section_index", 0),
                paragraphs=f.get("paragraphs", []),
                text=f.get("text", ""),
                linked_to_previous=f.get("linked_to_previous", False),
            )
            for f in data.get("footers", [])
        ]

        return cls(
            format=data.get("format", "unknown"),
            metadata=data.get("metadata", {}),
            layout=data.get("layout", {}),
            paragraphs=paragraphs,
            styles=styles,
            headers=headers,
            footers=footers,
            tables=data.get("tables", []),
        )
