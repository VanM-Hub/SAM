"""WP-01 — constitution_index (IP-3.1-001).

Index for the Constitution normative document. Delivers facets:
  Article, Principle, Constraint.
"""

from __future__ import annotations

from typing import List

from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem


def index_constitution(path: str, content: str) -> KnowledgeIndex:
    """Build the Constitution index from a markdown document."""
    base = load_index("constitution", path, "constitution", content)
    return _label_facets(base, "constitution")


def _label_facets(base: KnowledgeIndex, kind: str) -> KnowledgeIndex:
    remapped: List[KnowledgeItem] = []
    for it in base.all():
        low = it.section.lower()
        if any(k in low for k in ("article", "pasal")):
            label = "Article"
        elif any(k in low for k in ("principle", "prinsip")):
            label = "Principle"
        elif any(k in low for k in ("constraint", "batasan", "constraints")):
            label = "Constraint"
        else:
            label = "Article"
        remapped.append(
            KnowledgeItem(
                id=it.id,
                key=f"constitution.{label.lower()}",
                kind=kind,
                source=it.source,
                section=it.section,
                title=it.title,
                content=it.content,
                signature=it.signature,
                metadata={**it.metadata, "facet": label},
            )
        )
    return KnowledgeIndex(name="constitution", items=remapped)
