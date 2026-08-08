"""WP-21 - Governance Knowledge Expansion (IP-3.1-002).

Expands the Knowledge Index to support additional read-only governance
artifacts:

    Architecture Orders
    Engineering Verdicts
    Chief Architect Acceptance
    Certification Reports
    Milestone History

All remain read-only. This module provides lightweight index builders and
typed queries for the additional kinds. They reuse the immutable
KnowledgeItem/KnowledgeIndex primitives (WP-01) and do NOT add new mutable
state.
"""

from __future__ import annotations

from typing import Dict, List

from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem

# Supported expanded artifact kinds.
ARCH_ORDER = "arch_order"
VERDICT = "verdict"
ACCEPTANCE = "acceptance"
CERTIFICATION = "certification"
MILESTONE = "milestone"


def build_expanded_index(name: str, items: List[KnowledgeItem]) -> KnowledgeIndex:
    """Wrap additional governance artifacts into an immutable index."""
    return KnowledgeIndex(name=name, items=list(items))


def index_kind(name: str, records: List[dict]) -> KnowledgeIndex:
    """Build a KnowledgeIndex from plain dict records (read-only authors).

    Each record::
        {key, title, source, section(optional), kind_override(optional),
         content(optional), metadata(optional)}

    The index items are immutable KnowledgeItems; signatures are produced from
    the canonical content for change detection.
    """
    built: List[KnowledgeItem] = []
    for i, rec in enumerate(records):
        kind = rec.get("kind_override") or (rec.get("kind") or name)
        content = rec.get("content") or f"{rec.get('title', key_of(rec))}: {rec.get('section', '')}".strip()
        built.append(
            KnowledgeItem(
                key=rec["key"],
                kind=kind,
                source=rec.get("source", name),
                section=rec.get("section", ""),
                title=rec.get("title", rec["key"]),
                content=content,
                signature=_sig(content),
                metadata=rec.get("metadata") or {},
            )
        )
    return KnowledgeIndex(name=name, items=built)


def key_of(rec: dict) -> str:
    return rec.get("key", "")


def _sig(content: str) -> str:
    import hashlib

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class ExpandedKnowledgeQueries:
    """Typed read-only queries over the expanded index."""

    def __init__(self, index: KnowledgeIndex) -> None:
        self._index = index

    def arch_orders(self) -> List[KnowledgeItem]:
        return self._index.by_kind(ARCH_ORDER)

    def verdicts(self) -> List[KnowledgeItem]:
        return self._index.by_kind(VERDICT)

    def acceptances(self) -> List[KnowledgeItem]:
        return self._index.by_kind(ACCEPTANCE)

    def certifications(self) -> List[KnowledgeItem]:
        return self._index.by_kind(CERTIFICATION)

    def milestones(self) -> List[KnowledgeItem]:
        return self._index.by_kind(MILESTONE)

    def latest(self, kind: str) -> List[KnowledgeItem]:
        return self._index.by_kind(kind)
