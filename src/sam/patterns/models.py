"""Pattern data models for SAM Pattern Engine."""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid


class PatternSeverity(str, Enum):
    """Severity levels for pattern detections."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class PatternRule(BaseModel):
    """Rule definition for pattern detection.

    A rule defines conditions that must be met on KnowledgeFact records
    to trigger a pattern detection.
    """

    id: str
    name: str
    condition: str  # Human-readable description of the condition
    severity: PatternSeverity
    tags: List[str] = Field(default_factory=list)
    min_confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    enabled: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }


class PatternDetection(BaseModel):
    """A pattern detection event resulting from rule evaluation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    knowledge_fact_ids: List[str] = Field(default_factory=list)
    severity: PatternSeverity
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "str_strip_whitespace": True,
    }