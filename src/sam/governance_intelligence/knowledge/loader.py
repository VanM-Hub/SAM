"""WP-01 — Markdown loader for normative documents (IP-3.1-001).

Deterministic reader that loads a Markdown file into a simple section tree
(headings + their body text), so an index can tag each part with its source
path and section for full traceability.

This is intentionally minimal — no AI, no templates, no external deps. The
goal of WP-01 is a knowledge INDEX, not a rich renderer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from sam.governance_intelligence.knowledge.models import KnowledgeItem


@dataclass(frozen=True)
class MarkdownSection:
    """A markdown heading and the raw text carved out beneath it."""

    level: int
    heading: str
    body: str


def _heading_re() -> "re.Pattern[str]":
    return re.compile(r"^(#{1,6})\s+(.+?)\s*$")


def read_sections(content: str) -> List[MarkdownSection]:
    """Split markdown text into document-order sections.

    Each ``# Heading`` opens a section; its body collects the lines that
    follow until the next heading. Sections are returned in document order
    (top-down). Heading levels are preserved for hierarchy consumers.
    """
    lines = content.splitlines()
    sections: List[MarkdownSection] = []

    current_level = None
    current_heading = None
    body: List[str] = []

    def flush():
        nonlocal current_level, current_heading, body
        if current_heading is not None:
            sections.append(
                MarkdownSection(current_level, current_heading, "\n".join(body).strip())
            )
        current_level = None
        current_heading = None
        body = []

    for raw in lines:
        m = _heading_re().match(raw)
        if m:
            flush()
            current_level = len(m.group(1))
            current_heading = m.group(2).strip()
        else:
            if current_heading is not None:
                body.append(raw)
    flush()
    return sections


def build_items(path: str, kind: str, content: str) -> List[KnowledgeItem]:
    """Convert a markdown document into KnowledgeItems.

    Returns one item per top-level '#'...'#' section (level 1 to 6) with a
    stable content signature. Items are tagged with source=path and kind.
    """
    import hashlib

    sections = read_sections(content)
    items: List[KnowledgeItem] = []
    for idx, sec in enumerate(sections):
        text = sec.body or ""
        sig = hashlib.sha256(text.encode("utf-8")).hexdigest()
        items.append(
            KnowledgeItem(
                key=f"{kind}.section.{idx + 1}",
                kind=kind,
                source=path,
                section=sec.heading,
                title=sec.heading,
                content=text,
                signature=sig,
                metadata={"level": sec.level},
            )
        )
    return items


def load_index(name: str, path: str, kind: str, content: str) -> "KnowledgeIndex":
    from sam.governance_intelligence.knowledge.models import KnowledgeIndex

    return KnowledgeIndex(name=name, items=build_items(path, kind, content))
