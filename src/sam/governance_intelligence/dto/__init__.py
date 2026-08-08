"""dto — shared immutable DTOs (IP-3.1-001).

Cross-layer transfer objects shared between repositories, reasoning,
explanation, and gateway. Kept minimal and immutable.
"""

from sam.governance_intelligence.knowledge.models import KnowledgeItem, KnowledgeIndex

__all__ = ["KnowledgeItem", "KnowledgeIndex"]
