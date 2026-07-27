"""
Intelligence Models — Phase 1

Model data untuk Incident Detection, Root Cause Analysis, dan Recommendation.
"""

import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class IncidentSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Incident(BaseModel):
    """Insiden yang terdeteksi oleh IncidentDetector."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    title: str
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    source: str = "unknown"  # openclaw, runtime, plugin, log
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    status: str = "open"  # open, investigating, resolved, closed


class RootCause(BaseModel):
    """Akar penyebab insiden hasil RCA."""

    incident_id: str
    cause: str
    confidence: float = 0.5  # 0.0 - 1.0
    evidence: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None


class Recommendation(BaseModel):
    """Rekomendasi perbaikan untuk insiden."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    incident_id: str
    title: str
    description: str = ""
    workflow: Optional[str] = None  # workflow ID atau YAML
    confidence: float = 0.5
    risk: str = "medium"  # low, medium, high
    steps: List[str] = Field(default_factory=list)
