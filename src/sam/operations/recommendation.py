"""
Recommendation Engine — 'What should happen next?'

Input: Situation + History + Knowledge
Output: Rekomendasi aksi.

BUKAN observasi.
BUKAN cerita.
Rekomendasi adalah KEPUTUSAN yang disarankan.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Recommendation:
    """Satu rekomendasi untuk operator."""
    action: str                         # "restart", "backup", "upgrade", "review", "approve"
    target: str                         # "OpenClaw runtime", "workspace"
    reason: str                         # "Memory usage increased"
    impact: str                         # "Restart resolves within 2 minutes"
    priority: int = 50                  # 100=immediate, 80=soon, 50=normal, 20=background
    confidence: float = 0.8
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def display(self) -> str:
        return "{} — {}".format(self.action, self.reason)


class RecommendationPolicy:
    """Menjawab: 'What should happen next?'"""

    def __init__(self, experience_engine=None):
        self._ee = experience_engine

    def get_recommendations(self, situation: str = "",
                            limit: int = 5) -> List[Recommendation]:
        """Dapatkan rekomendasi berdasarkan situasi terkini."""
        recs = []

        try:
            if self._ee:
                # Dari knowledge engine — insight-based
                knowledge = self._ee.build_knowledge()
                if knowledge and knowledge.items:
                    for item in knowledge.items[:3]:
                        if getattr(item, 'severity', '') == "recommendation":
                            recs.append(Recommendation(
                                action="Review",
                                target=item.title[:40],
                                reason=item.title[:60],
                                impact="Confidence: {:.0f}%".format(
                                    item.confidence * 100 if item.confidence else 0
                                ),
                                priority=50,
                                confidence=item.confidence or 0.5,
                            ))

            # Situasi-based
            if situation == "needs_attention":
                recs.append(Recommendation(
                    action="Review",
                    target="recent activity",
                    reason="Items require your attention",
                    impact="Review takes approximately 2 minutes",
                    priority=50,
                ))

            if situation == "action_required":
                recs.append(Recommendation(
                    action="Take action",
                    target="pending items",
                    reason="Immediate review needed",
                    impact="Delaying may affect operations",
                    priority=80,
                ))

            # Fallback — tidak ada rekomendasi
            if not recs:
                recs.append(Recommendation(
                    action="No recommendation",
                    target="",
                    reason="Everything is operating normally.",
                    impact="",
                    priority=10,
                ))

        except Exception:
            pass

        # Sort by priority
        recs.sort(key=lambda r: r.priority, reverse=True)
        return recs[:limit]
