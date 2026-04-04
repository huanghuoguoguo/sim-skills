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
