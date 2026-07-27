from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class KnowledgeType(str, Enum):
    FACT = "fact"
    PATTERN = "pattern"
    RECOMMENDATION = "recommendation"
    INSIGHT = "insight"
    LESSON = "lesson"
    TIP = "tip"


class KnowledgeEntry(BaseModel):
    """Satu item pengetahuan."""
    id: str
    type: KnowledgeType
    title: str                          # Judul yang dapat dibaca
    content: str                        # Penjelasan lengkap
    confidence: float = 0.0  # 0-1
    source: str                         # Dari mana knowledge ini berasal
    timestamp: datetime
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InsightEntry(BaseModel):
    """Insight — pola yang lebih tinggi."""
    id: str
    title: str
    description: str
    severity: str  # info, warning, critical
    evidence: List[str] = Field(default_factory=list)
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeModel(BaseModel):
    """ViewModel untuk Knowledge Experience."""
    entries: List[KnowledgeEntry]
    insights: List[InsightEntry]
    total_entries: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True

    @property
    def recommendation_count(self) -> int:
        return sum(1 for e in self.entries if e.type == KnowledgeType.RECOMMENDATION)

    @property
    def insight_count(self) -> int:
        return len(self.insights)
