"""WP-01 — governance_index (IP-3.1-001).

Index for governance normatives. Delivers facets:
  Workflow, Policy, Approval, Runtime.
"""

from __future__ import annotations

from typing import List

from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem


def index_governance(path: str, content: str) -> KnowledgeIndex:
    """Build the Governance index from a markdown document."""
    base = load_index("governance", path, "governance", content)
    remapped: List[KnowledgeItem] = []
    for it in base.all():
        low = it.section.lower()
        if any(k in low for k in ("workflow", "alur")):
            label = "Workflow"
        elif any(k in low for k in ("policy", "kebijakan")):
            label = "Policy"
        elif any(k in low for k in ("approval", "persetujuan")):
            label = "Approval"
        elif any(k in low for k in ("runtime", "operational", "operasi")):
            label = "Runtime"
        else:
            label = "Policy"
        remapped.append(
            KnowledgeItem(
                id=it.id,
                key=f"governance.{label.lower()}",
                kind="governance",
                source=it.source,
                section=it.section,
                title=it.title,
                content=it.content,
                signature=it.signature,
                metadata={**it.metadata, "facet": label},
            )
        )
    return KnowledgeIndex(name="governance", items=remapped)
