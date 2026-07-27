"""
Presentation Engine — Layer yang mengubah Semantic State + Decision menjadi Human Narrative.

BUKAN Storyteller.
BUKAN Narrative Builder.
Presentation Engine menerjemahkan keputusan dan keadaan menjadi bahasa manusia.

Input: Situation (semantic) + Decision (SAM action) + Mission State
Output: Kalimat yang muncul di layar.

Sepenuhnya terpisah dari Runtime.
Sepenuhnya terpisah dari Telemetry.
HANYA membaca Decision Model.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from .models import Narrative, NarrativeImportance, NarrativeType


# ============================================================================
# Decision Model — Keputusan SAM (bukan observasi)
# ============================================================================

@dataclass
class Decision:
    """Keputusan yang diambil SAM.

    SAM hanya muncul sebagai subjek di sini — saat SAM BERTINDAK.
    """
    action: str                         # "recommend", "block", "postpone", "approve", "recover", "escalate", "ignore"
    target: str                         # "OpenClaw runtime", "workspace deployment", "plugin update"
    reason: str                         # "health check failed", "policy violation"
    confidence: float = 1.0
    decision_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    narrative: Optional[str] = None     # "SAM recommends restarting OpenClaw."


# ============================================================================
# Presentation — Apa yang muncul di layar
# ============================================================================

@dataclass
class Presentation:
    """Tampilan layar — BAHASA MANUSIA.

    Tidak ada SAM di sini kecuali SAM benar-benar bertindak.
    """
    # Empat pertanyaan Home
    system_condition: str = ""      # "Operating normally." | "Deployment in progress."
    current_activity: str = ""      # "A new deployment pattern was identified."
    sam_action: str = ""            # Hanya diisi jika SAM bertindak. "" jika tidak.
    user_action_needed: str = ""    # "No action required." | "Approval required."

    # Detail
    detail: str = ""
    recommendations: List[str] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)

    # Narrative (untuk UI rendering)
    narrative: Optional[Narrative] = None
    attention_label: str = "Normal"  # "Immediate" | "Soon" | "Normal" | "Background"

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# PresentationRenderer
# ============================================================================

# Mapping Situation → Human Language untuk Mission Target
SITUATION_TO_CONDITION = {
    "everything_healthy": ("Operating normally.", "No action required."),
    "deployment_running": ("Deployment in progress.", "Everything is running."),
    "waiting_approval": ("Deployment requires approval.", "Approval needed to continue."),
    "recovering": ("Automatic recovery in progress.", "No intervention required."),
    "learning": ("New patterns are being analyzed.", "No action required."),
    "needs_attention": ("Needs your attention.", "Review recommended."),
    "action_required": ("Action required.", "Immediate review needed."),
}

SITUATION_TO_ACTIVITY = {
    "everything_healthy": "Monitoring continues. No issues detected.",
    "deployment_running": "Workspace deployment is running.",
    "waiting_approval": "Waiting for approval on pending deployment.",
    "recovering": "Automatic recovery is active.",
    "learning": "Analyzing new operational patterns.",
    "needs_attention": "Review recommended for one or more items.",
    "action_required": "Action needed to proceed.",
}

ATTENTION_LABELS = {
    100: "Immediate",
    80: "Soon",
    50: "Normal",
    20: "Background",
}


class PresentationRenderer:
    """Mengubah semantic state + decision menjadi tampilan manusia."""

    def __init__(self):
        pass

    def build(self, situation_str: str, attention_score: int = 0,
              decision: Optional[Decision] = None,
              progress_percent: int = 0,
              estimated_time: str = "",
              detail_level2: str = "") -> Presentation:
        """Bangun Presentation dari semantic state.

        Args:
            situation_str: Salah satu dari 7 semantic state
            attention_score: 100/80/50/20
            decision: Ada keputusan SAM? (None jika tidak)
            progress_percent: Progress deployment (0 jika tidak relevan)
            estimated_time: ETA ("" jika tidak relevan)
        """
        condition, user_action = SITUATION_TO_CONDITION.get(
            situation_str, ("Status unknown.", "No action required.")
        )
        activity = SITUATION_TO_ACTIVITY.get(
            situation_str, "Monitoring."
        )

        # Progress untuk deployment
        if situation_str == "deployment_running" and progress_percent > 0:
            condition = "Deployment in progress. {}%".format(progress_percent)
            if estimated_time:
                condition += " — ETA {}".format(estimated_time)

        # SAM action — hanya muncul jika ada decision
        sam_action = ""
        if decision:
            sam_action = "{} {}".format(
                decision.action.capitalize(),
                decision.target,
            )

        # Attention label
        attention_label = ATTENTION_LABELS.get(attention_score, "Normal")

        # Narrative
        narrative = Narrative(
            title=condition,
            summary="{} {}".format(condition, user_action),
            details=detail_level2,
            importance=(
                NarrativeImportance.CRITICAL if attention_score >= 80
                else NarrativeImportance.ATTENTION if attention_score >= 50
                else NarrativeImportance.INFORMATION
            ),
        )

        return Presentation(
            system_condition=condition,
            current_activity=activity,
            sam_action=sam_action,
            user_action_needed=user_action,
            detail=detail_level2,
            attention_label=attention_label,
            narrative=narrative,
        )
