"""Pydantic models for Knowledge System."""

from datetime import datetime
from uuid import UUID, uuid4
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    """Represents a knowledge document stored as markdown."""

    id: UUID = Field(default_factory=uuid4)
    path: str  # Relative path from repository root
    title: str
    version: str
    status: str
    knowledge_type: str  # e.g., Concept, Operational, Reference
    evidence_level: str  # e.g., Verified, Observed, Experimental
    confidence: str  # e.g., High, Medium, Low
    owner: str
    last_updated: datetime
    related_documents: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)
    content: str  # Full markdown content
    metadata: Dict[str, str] = Field(default_factory=dict)


class KnowledgeRelationship(BaseModel):
    """Represents a relationship between two knowledge facts."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    target_id: UUID
    relationship_type: str  # e.g., "supports", "depends_on", "requires", "contradicts", "related_to"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class KnowledgeFact(BaseModel):
    """Represents an atomic knowledge fact extracted from documents."""

    id: UUID = Field(default_factory=uuid4)
    document_id: UUID  # Source document
    statement: str  # The factual statement
    category: str  # e.g., "capability", "provider", "model", "constraint"
    confidence: float  # 0.0 - 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class KnowledgeHistory(BaseModel):
    """Represents a versioned history of changes to a knowledge fact."""

    id: UUID = Field(default_factory=uuid4)
    knowledge_id: UUID
    version: int
    payload_snapshot: Dict[str, Any]  # Full fact snapshot
    changed_by: str  # user or system
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_type: str  # "created", "updated", "deleted"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }
