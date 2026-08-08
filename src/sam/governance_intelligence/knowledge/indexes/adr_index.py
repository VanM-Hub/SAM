"""WP-01 — adr_index (IP-3.1-001).

Indexes all ACCEPTED Architecture Decision Records (ADR). Only Accepted ADRs
are included; Draft/Proposed/Rejected are excluded per the directive.
"""

from __future__ import annotations

from typing import List, Sequence

from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem


def index_adr(path: str, content: str, status: str = "Accepted") -> KnowledgeIndex:
    """Build an ADR index. If ``status`` is 'Accepted', only include items
    whose metadata 'status' equals Accepted (callers may pre-filter)."""
    from sam.governance_intelligence.knowledge.loader import load_index

    base = load_index("adr", path, "adr", content)
    # Only Accepted items survive.
    kept: List[KnowledgeItem] = []
    for it in base.all():
        item_status = it.metadata.get("status", "Accepted")
        if status.lower() == "accepted" and item_status.lower() != "accepted":
            continue
        kept.append(it)
    return KnowledgeIndex(name="adr", items=kept)


def accept_all(items: Sequence[KnowledgeItem]) -> KnowledgeIndex:
    """Helper to mark an adr index as accepted explicitly."""
    return KnowledgeIndex(name="adr", items=list(items))
