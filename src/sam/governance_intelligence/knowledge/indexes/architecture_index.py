"""WP-01 — architecture_index (IP-3.1-001).

Indexes architecture normatives: Architecture Order, Roadmap, Milestone,
Specification.
"""

from __future__ import annotations

from typing import List

from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem


def index_architecture(path: str, content: str) -> KnowledgeIndex:
    """Build the Architecture index from a markdown document."""
    base = load_index("architecture", path, "architecture", content)
    remapped: List[KnowledgeItem] = []
    for it in base.all():
        low = it.section.lower()
        if any(k in low for k in ("order", "urutan")):
            label = "ArchitectureOrder"
        elif any(k in low for k in ("roadmap", "peta jalan")):
            label = "Roadmap"
        elif any(k in low for k in ("milestone", "tonggak")):
            label = "Milestone"
        elif any(k in low for k in ("spec", "specification", "spesifikasi")):
            label = "Specification"
        else:
            label = "Milestone"
        remapped.append(
            KnowledgeItem(
                id=it.id,
                key=f"architecture.{label.lower()}",
                kind="architecture",
                source=it.source,
                section=it.section,
                title=it.title,
                content=it.content,
                signature=it.signature,
                metadata={**it.metadata, "facet": label},
            )
        )
    return KnowledgeIndex(name="architecture", items=remapped)
