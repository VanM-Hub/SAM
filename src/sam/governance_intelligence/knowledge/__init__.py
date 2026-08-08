"""governance_intelligence.knowledge — WP-01..03 (IP-3.1-001).

Foundation knowledge layer: converts normative documents into a queryable,
immutable Knowledge Model.
"""

from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem
from sam.governance_intelligence.knowledge.loader import build_items, load_index, read_sections
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    QueryOnlyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.knowledge.query import KnowledgeQueryAPI, QueryResult
from sam.governance_intelligence.knowledge.indexes import (
    facets,
    index_adr,
    index_architecture,
    index_constitution,
    index_governance,
    index_mission,
)

__all__ = [
    "ADRRepository",
    "EvidenceRepository",
    "KnowledgeIndex",
    "KnowledgeItem",
    "KnowledgeQueryAPI",
    "MissionRepository",
    "PolicyRepository",
    "QueryOnlyRepository",
    "QueryResult",
    "RuntimeRepository",
    "build_items",
    "facets",
    "index_adr",
    "index_architecture",
    "index_constitution",
    "index_governance",
    "index_mission",
    "load_index",
    "read_sections",
]
