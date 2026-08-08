"""WP-01 — mission_index (IP-3.1-001).

Index for the Mission normative document. Delivers facets:
  Mission, Objective, Scope, Lifecycle.

The index collapses markdown sections under ``Mission``/``Objective``/
``Scope``/``Lifecycle`` labels so the KnowledgeIndex can be queried by facet
with ``by_key('mission.objective')`` etc.
"""

from __future__ import annotations

from typing import Dict, List

from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem

# Heading keywords -> facet label.
_FACET_BY_KEYWORD = {
    "objective": "Objective",
    "tujuan": "Objective",
    "scope": "Scope",
    "ruang lingkup": "Scope",
    "lifecycle": "Lifecycle",
    "siklus hidup": "Lifecycle",
    "mission": "Mission",
    "misi": "Mission",
}


def _facet(heading: str) -> str:
    low = heading.lower()
    for kw, label in _FACET_BY_KEYWORD.items():
        if kw in low:
            return label
    return "Mission"


def index_mission(path: str, content: str) -> KnowledgeIndex:
    """Build the Mission index from a markdown document."""
    base = load_index("mission", path, "mission", content)
    remapped: List[KnowledgeItem] = []
    for it in base.all():
        label = _facet(it.section)
        key = f"mission.{label.lower()}"
        remapped.append(
            KnowledgeItem(
                id=it.id,
                key=key,
                kind="mission",
                source=it.source,
                section=it.section,
                title=it.title,
                content=it.content,
                signature=it.signature,
                metadata={**it.metadata, "facet": label},
            )
        )
    return KnowledgeIndex(name="mission", items=remapped)


def facets(index: KnowledgeIndex) -> Dict[str, List[KnowledgeItem]]:
    """Group items by facet label."""
    result: Dict[str, List[KnowledgeItem]] = {}
    for it in index.all():
        label = it.metadata.get("facet", "Mission")
        result.setdefault(label, []).append(it)
    return result
