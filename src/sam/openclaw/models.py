"""
OpenClaw Models — Phase 1

Model data untuk integrasi dengan OpenClaw Runtime.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class OpenClawStatus(str, Enum):
    """Status komponen OpenClaw."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class OpenClawComponent(BaseModel):
    """Satu komponen dalam ekosistem OpenClaw."""

    name: str
    status: OpenClawStatus = OpenClawStatus.UNKNOWN
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class OpenClawHealth(BaseModel):
    """Snapshot health seluruh OpenClaw runtime."""

    workspace: str = ""
    runtime: OpenClawStatus = OpenClawStatus.UNKNOWN
    components: List[OpenClawComponent] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OpenClawWorkspace(BaseModel):
    """OpenClaw workspace yang terdeteksi."""

    path: str
    version: Optional[str] = None
    detected: bool = False
    health: Optional[OpenClawHealth] = None
