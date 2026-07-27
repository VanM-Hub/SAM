from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class HistoryEntryType(str, Enum):
    TASK = "task"
    SYSTEM = "system"
    INCIDENT = "incident"
    RECOVERY = "recovery"
    APPROVAL = "approval"
    CONFIGURATION = "configuration"
    PLUGIN = "plugin"
    KNOWLEDGE = "knowledge"
    USER = "user"


class HistoryEntrySeverity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HistoryEntry(BaseModel):
    """Satu item riwayat."""
    id: str
    type: HistoryEntryType
    severity: HistoryEntrySeverity
    title: str
    description: Optional[str] = None
    timestamp: datetime
    duration_ms: Optional[float] = None
    correlation_id: Optional[str] = None
    user: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HistoryDay(BaseModel):
    """Kelompok riwayat per hari."""
    date: datetime
    entries: List[HistoryEntry]
    count: int


class HistoryFilter(BaseModel):
    """Filter untuk riwayat."""
    types: List[HistoryEntryType] = Field(default_factory=list)
    severities: List[HistoryEntrySeverity] = Field(default_factory=list)
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    query: Optional[str] = None
    limit: int = 1000


class HistoryModel(BaseModel):
    """ViewModel untuk halaman History."""
    days: List[HistoryDay]
    total: int
    filtered: int
    filters: HistoryFilter
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True
