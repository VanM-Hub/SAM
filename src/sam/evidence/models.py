"""Evidence data models for SAM Evidence Store."""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class EvidenceType(str, Enum):
    """Types of operational evidence that capabilities can produce."""

    HEALTH_CHECK = "health_check"
    CONFIG_VALIDATION = "config_validation"
    PROVIDER_TEST = "provider_test"
    RUNTIME_OBSERVATION = "runtime_observation"
    FILESYSTEM_CHECK = "filesystem_check"
    NETWORK_CHECK = "network_check"
    PERMISSION_CHECK = "permission_check"
    API_RESPONSE = "api_response"
    EXECUTION_TRACE = "execution_trace"
    ERROR_EVENT = "error_event"
    DECISION_OUTCOME = "decision_outcome"
    PATTERN_MATCH = "pattern_match"
    ANOMALY_DETECTED = "anomaly_detected"
    RECOVERY_ACTION = "recovery_action"
    CUSTOM = "custom"


class EvidenceStatus(str, Enum):
    """Lifecycle status of an evidence record."""

    COLLECTED = "collected"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class Evidence(BaseModel):
    """Immutable evidence record produced by a capability execution.

    Attributes:
        id: Unique identifier for this evidence record.
        capability_id: ID of the capability that produced this evidence.
        execution_id: Execution context ID linking to the capability run.
        type: Categorization of the evidence.
        status: Current lifecycle status.
        confidence: Confidence score between 0.0 and 1.0.
        payload: Arbitrary structured data captured as evidence.
        source: Origin of the evidence (e.g., "filesystem", "api", "runtime").
        timestamp: When the evidence was collected.
        metadata: Additional unstructured context.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    capability_id: str
    execution_id: str
    type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    confidence: float = Field(ge=0.0, le=1.0, default=1.0)
    payload: Dict[str, Any] = Field(default_factory=dict)
    source: str = "runtime"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }