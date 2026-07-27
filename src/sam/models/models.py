"""Data models for the SAM Framework.

All models inherit from Entity and are implemented using Pydantic.
"""

from datetime import datetime
from uuid import UUID
from typing import List, Dict, Optional, Any

from pydantic import BaseModel, Field, ConfigDict


class CapabilityDescriptor(BaseModel):
    """
    Descriptor for a SAM capability, used by the Registry and Factory.

    This model is intentionally lightweight and does not inherit from Entity
    to avoid coupling with the persistence layer.

    Example:
        {
            "id": "openclaw.health-checks",
            "version": "1.0.0",
            "implementation": "sam.capabilities.health_checks.HealthCheckCapability",
            "capability_type": "observation.health-checks",
            "risk_level": "Low",
            "permissions": [],
            "dependencies": [],
            "tags": ["health", "observation", "openclaw"],
            "description": "Collects evidence and reports operational health without modifying state.",
            "source_document": "modules/openclaw/capabilities/health-checks.md",
            "enabled": true
        }
    """
    id: str
    version: str
    implementation: str
    capability_type: str
    risk_level: str
    permissions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    description: str
    source_document: str
    enabled: bool = True


class Entity(BaseModel):
    """Base entity with common fields."""
    id: UUID
    created_at: datetime
    version: str = Field(default="1.0")

    model_config = ConfigDict(
        frozen=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        },
    )


class Capability(Entity):
    """Represents a registered executable capability."""
    capability_id: str
    name: str
    description: str
    owner: str
    version: str
    permissions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    risk_level: str  # e.g., low, medium, high
    rollback_supported: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Workflow(Entity):
    """Represents a workflow definition."""
    workflow_id: str
    name: str
    version: str
    entry_capability: str  # capability_id of the first step
    steps: List[str]  # list of capability_ids in order
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Execution(Entity):
    """Represents one workflow execution."""
    execution_id: str
    workflow_id: str
    status: str  # e.g., pending, running, completed, failed, rolled_back
    started_at: datetime
    completed_at: Optional[datetime] = None
    rollback_id: Optional[str] = None  # execution_id of rollback if applicable
    context: Dict[str, Any] = Field(default_factory=dict)


class Evidence(Entity):
    """Represents an observed fact."""
    source: str  # identifier of the source (e.g., capability_id, sensor)
    evidence_type: str
    confidence: float  # 0.0 to 1.0
    timestamp: datetime
    payload: Dict[str, Any] = Field(default_factory=dict)


class AuditEvent(Entity):
    """Represents an operational event."""
    execution_id: str
    capability_id: str
    event_type: str
    severity: str  # e.g., info, warning, error, critical
    timestamp: datetime
    payload: Dict[str, Any] = Field(default_factory=dict)


class Knowledge(Entity):
    """Represents institutional knowledge."""
    title: str
    category: str
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float  # 0.0 to 1.0
    content: Dict[str, Any] = Field(default_factory=dict)


class Pattern(Entity):
    """Represents recurring operational behavior."""
    name: str
    observations: int  # number of times observed
    confidence: float  # 0.0 to 1.0
    recommendation: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Recommendation(Entity):
    """Represents a rule-based recommendation."""
    source_pattern: str  # pattern_id that generated this recommendation
    priority: str  # e.g., low, medium, high, critical
    recommendation: str
    rationale: str
    confidence: float  # 0.0 to 1.0


class ReasoningTrace(Entity):
    """Represents an entire diagnostic reasoning process."""
    symptom: str
    evidence: List[str] = Field(default_factory=list)  # list of evidence_ids
    hypotheses: List[str] = Field(default_factory=list)  # hypothesis descriptions
    rejected: List[str] = Field(default_factory=list)  # rejected hypothesis descriptions
    conclusion: str
    confidence: float  # 0.0 to 1.0


class MemoryRecord(Entity):
    """Represents historical operational memory."""
    execution_id: str
    category: str  # e.g., execution, performance, error
    summary: str
    references: List[str] = Field(default_factory=list)  # list of related record IDs