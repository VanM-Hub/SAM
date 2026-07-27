"""
Situation Detection Engine — mengenali situasi, bukan membaca event.

Hanya 7 situasi. Bukan dua puluh status.
Manusia berpikir dalam situasi, bukan dalam komponen.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Situation(str, Enum):
    """Tepat 7 situasi. Tidak lebih."""
    EVERYTHING_HEALTHY = "everything_healthy"
    DEPLOYMENT_RUNNING = "deployment_running"
    WAITING_APPROVAL = "waiting_approval"
    RECOVERING = "recovering"
    LEARNING = "learning"
    NEEDS_ATTENTION = "needs_attention"
    ACTION_REQUIRED = "action_required"


SITUATION_LABELS = {
    Situation.EVERYTHING_HEALTHY: ("SAM is healthy.", "No action required."),
    Situation.DEPLOYMENT_RUNNING: ("Deployment in progress.", "SAM is working."),
    Situation.WAITING_APPROVAL: ("SAM needs your approval.", "No execution will continue until approval is given."),
    Situation.RECOVERING: ("SAM is recovering.", "Systems are stabilizing."),
    Situation.LEARNING: ("SAM is learning.", "New patterns are being analyzed."),
    Situation.NEEDS_ATTENTION: ("SAM needs attention.", "Something requires your review."),
    Situation.ACTION_REQUIRED: ("Action required.", "Immediate review needed."),
}

SITUATION_ICONS = {
    Situation.EVERYTHING_HEALTHY: "\u2705",
    Situation.DEPLOYMENT_RUNNING: "\U0001f3d7\ufe0f",
    Situation.WAITING_APPROVAL: "\u26a0\ufe0f",
    Situation.RECOVERING: "\U0001f504",
    Situation.LEARNING: "\U0001f9e0",
    Situation.NEEDS_ATTENTION: "\U0001f4a1",
    Situation.ACTION_REQUIRED: "\U0001f6a8",
}

SITUATION_COLORS = {
    Situation.EVERYTHING_HEALTHY: "#4ae04a",
    Situation.DEPLOYMENT_RUNNING: "#6aaae0",
    Situation.WAITING_APPROVAL: "#e0c06a",
    Situation.RECOVERING: "#e0a06a",
    Situation.LEARNING: "#a06ae0",
    Situation.NEEDS_ATTENTION: "#e0c06a",
    Situation.ACTION_REQUIRED: "#e06a6a",
}


@dataclass
class SituationReport:
    """Hasil deteksi situasi."""
    situation: Situation
    label: str
    description: str
    icon: str
    color: str
    attention_score: int = 0
    focus_message: str = ""           # "SAM is healthy."
    focus_detail: str = ""            # "Watching OpenClaw."
    action_message: str = ""          # "No action required."
    progress_percent: int = 0          # 0-100, untuk deployment
    estimated_time: str = ""           # "6 minutes"
    detail_level2: str = ""            # Level 2: teknis, hanya jika diklik
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SituationEngine:
    """Mendeteksi situasi dari Experience Model.

    BUKAN dari Runtime.
    HANYA dari Experience Model → Narrative Engine.
    """

    def __init__(self, experience_engine):
        self._ee = experience_engine

    def detect(self) -> SituationReport:
        """Deteksi situasi saat ini.

        Prioritaskan:
        1. Action Required
        2. Waiting Approval
        3. Needs Attention
        4. Recovering
        5. Deployment Running
        6. Learning
        7. Everything Healthy
        """
        try:
            home = self._ee.build_home()
            work = self._ee.build_work()
            narrative = self._ee.build_narrative_home()

            attention_count = narrative.attention_count if narrative else 0
            action_count = narrative.action_count if narrative else 0

            pending_approvals = 0
            deployment_running = False
            deployment_progress = 0
            deployment_eta = ""
            deployment_name = ""

            if work and work.items:
                for w in work.items:
                    if w.approval_needed:
                        pending_approvals += 1
                    if w.status == "running":
                        deployment_running = True
                        deployment_name = w.title
                        if w.progress:
                            deployment_progress = w.progress.percent
                            deployment_eta = w.progress.estimated_remaining or ""

            # Cek situasi — prioritas
            if action_count > 0 or pending_approvals > 0 or (home.attention and home.attention.needs_attention and "immediate" in home.attention.message.lower()):
                sit = Situation.ACTION_REQUIRED
            elif pending_approvals > 0:
                sit = Situation.WAITING_APPROVAL
            elif attention_count > 0 or (home.attention and home.attention.needs_attention):
                sit = Situation.NEEDS_ATTENTION
            elif home.health and home.health.status.value == "recovering":
                sit = Situation.RECOVERING
            elif deployment_running:
                sit = Situation.DEPLOYMENT_RUNNING
            elif home.health and home.health.status.value == "learning":
                sit = Situation.LEARNING
            else:
                sit = Situation.EVERYTHING_HEALTHY

            label, desc = SITUATION_LABELS[sit]

            # Focus message
            if sit == Situation.EVERYTHING_HEALTHY:
                focus_msg = "SAM is healthy."
                focus_detail = "Watching OpenClaw."
                action_msg = "No action required."
            elif sit == Situation.DEPLOYMENT_RUNNING:
                focus_msg = "{} in progress.".format(deployment_name or "Deployment")
                focus_detail = ""
                action_msg = "SAM is working."
            elif sit == Situation.WAITING_APPROVAL:
                focus_msg = "SAM needs your approval."
                focus_detail = ""
                action_msg = "No execution will continue until approval is given."
            elif sit == Situation.RECOVERING:
                focus_msg = "SAM is recovering."
                focus_detail = ""
                action_msg = "No manual action required."
            elif sit == Situation.LEARNING:
                focus_msg = "SAM is learning."
                focus_detail = "New patterns are being analyzed."
                action_msg = "No action required."
            elif sit == Situation.NEEDS_ATTENTION:
                focus_msg = home.attention.message if home.attention else "SAM needs attention."
                focus_detail = home.attention.reason if hasattr(home.attention, 'reason') else ""
                action_msg = "Review recommended."
            elif sit == Situation.ACTION_REQUIRED:
                focus_msg = "Action required."
                focus_detail = home.attention.message if home.attention and home.attention.needs_attention else ""
                action_msg = "Immediate review needed."
            else:
                focus_msg = "SAM is operating."
                focus_detail = ""
                action_msg = ""

            # Detail level 2 (hanya jika diklik)
            detail2 = ""
            if work and work.items:
                lines = ["Active work:"]
                for w in work.items[:5]:
                    lines.append("  - {}: {}".format(w.title, w.status))
                    if w.progress:
                        lines.append("    Progress: {}%".format(w.progress.percent))
                detail2 = "\n".join(lines)

            # Attention score
            score_map = {
                Situation.ACTION_REQUIRED: 100,
                Situation.WAITING_APPROVAL: 80,
                Situation.NEEDS_ATTENTION: 70,
                Situation.RECOVERING: 60,
                Situation.DEPLOYMENT_RUNNING: 50,
                Situation.LEARNING: 30,
                Situation.EVERYTHING_HEALTHY: 10,
            }

            return SituationReport(
                situation=sit,
                label=label,
                description=desc,
                icon=SITUATION_ICONS[sit],
                color=SITUATION_COLORS[sit],
                attention_score=score_map.get(sit, 10),
                focus_message=focus_msg,
                focus_detail=focus_detail,
                action_message=action_msg,
                progress_percent=deployment_progress if sit == Situation.DEPLOYMENT_RUNNING else 0,
                estimated_time=deployment_eta if sit == Situation.DEPLOYMENT_RUNNING else "",
                detail_level2=detail2,
            )

        except Exception:
            return SituationReport(
                situation=Situation.EVERYTHING_HEALTHY,
                label="SAM is operating.",
                description="Status unknown.",
                icon="\u2753",
                color="#606070",
                attention_score=0,
                focus_message="SAM is operating.",
                action_message="No action required.",
            )
