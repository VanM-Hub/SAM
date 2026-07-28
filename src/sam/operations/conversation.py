"""
ConversationObject — Model domain tunggal untuk seluruh pengalaman pengguna.

Ini adalah satu-satunya representasi keadaan operasional yang dipahami manusia.
TIDAK ada lagi builder paralel.
TIDAK ada lagi experience yang bikin narasi sendiri.

Sumber kebenaran untuk: Desktop, CLI, API, Voice, Email, Slack, LLM.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from datetime import datetime


@dataclass(frozen=True)
class ConversationObject:
    """Satu-satunya representasi keadaan operasional.

    Immutable. Dibangun oleh SystemAnalyzer.
    Dibaca oleh Conversation API → Renderer → HumanAnswer.

    BUKAN DTO. Ini domain model. Semua penalaran ada di sini.
    """

    # ====================================================================
    # Situasi
    # ====================================================================
    situation: str = "unknown"              # "everything_healthy" | "deployment_running" | ...
    situation_summary: str = ""             # "Operating normally."
    situation_severity: str = "information" # "information" | "attention" | "action_required" | "critical"

    # ====================================================================
    # Mission
    # ====================================================================
    mission_target: str = "Workspace"       # Apa yang dijaga
    mission_condition: str = "Operating normally."
    mission_activity: str = "Monitoring continues."

    # ====================================================================
    # SAM — hanya jika SAM bertindak
    # ====================================================================
    sam_action: str = ""                    # "Restarting OpenClaw" — hanya jika ada
    sam_decision: str = ""                  # "recommend", "block", "approve", "recover"
    sam_reason: str = ""                    # Kenapa SAM mengambil keputusan itu
    sam_confidence: float = 0.0

    # ====================================================================
    # Facts — apa yang diketahui pasti
    # ====================================================================
    facts: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)

    # ====================================================================
    # Actions — apa yang perlu dilakukan
    # ====================================================================
    user_action_needed: str = "No action required."
    user_actions: List[str] = field(default_factory=list)

    # ====================================================================
    # Risks + Predictions
    # ====================================================================
    risks: List[str] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)

    # ====================================================================
    # Recommendations
    # ====================================================================
    recommendations: List[str] = field(default_factory=list)

    # ====================================================================
    # Activity History — perubahan terakhir
    # ====================================================================
    activity_changes: List[str] = field(default_factory=list)
    activity_count: int = 0

    # ====================================================================
    # Technical
    # ====================================================================
    technical_details: str = ""
    attention_label: str = "Normal"     # "Immediate" | "Soon" | "Normal" | "Background"
    attention_score: int = 20

    # ====================================================================
    # RCA — Root Cause Analysis (OP-72)
    # ====================================================================
    root_cause: Optional[dict] = None  # dict serialisasi RootCauseReport

    # ====================================================================
    # Decision Layer (Sprint 3)
    # ====================================================================
    decisions: List[str] = field(default_factory=list)        # proposal texts
    decision_details: Optional[dict] = None                    # serialized DecisionPackage
    impact_details: Optional[dict] = None                      # serialized ImpactPackage
    alternatives_details: Optional[dict] = None                # serialized AlternativesPackage

    # Action Center counts
    approval_pending_count: int = 0
    approval_approved_count: int = 0
    approval_rejected_count: int = 0

    # ====================================================================
    # Metadata
    # ====================================================================
    confidence: float = 0.8             # Keyakinan UnderstandingEngine
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
