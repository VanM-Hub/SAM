"""WP-01 — index package (IP-3.1-001).

Concrete document indexes. Each converts a normative document into a
``KnowledgeIndex`` so the framework can query it without knowing the source
format.
"""

from sam.governance_intelligence.knowledge.indexes.mission_index import facets, index_mission
from sam.governance_intelligence.knowledge.indexes.constitution_index import index_constitution
from sam.governance_intelligence.knowledge.indexes.governance_index import index_governance
from sam.governance_intelligence.knowledge.indexes.adr_index import accept_all, index_adr
from sam.governance_intelligence.knowledge.indexes.architecture_index import index_architecture

__all__ = [
    "accept_all",
    "facets",
    "index_adr",
    "index_architecture",
    "index_constitution",
    "index_governance",
    "index_mission",
]
