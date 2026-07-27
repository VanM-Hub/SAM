"""
Attention Engine — memberi bobot pada setiap event/situasi.

Internal score: 100/80/50/20
Presentation label: Immediate/Soon/Normal/Background

UI tidak boleh menampilkan angka.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional


SCORE_TO_LABEL = {
    100: "Immediate",
    80: "Soon",
    50: "Normal",
    20: "Background",
}


class AttentionScore(IntEnum):
    """Skala perhatian — internal. UI pakai label."""
    IMMEDIATE = 100      # Harus lihat sekarang
    IMPORTANT = 80       # Signifikan, review hari ini
    NORMAL = 50          # Biasa, tidak mendesak
    BACKGROUND = 20      # FYI saja


@dataclass(frozen=True)
class AttentionItem:
    """Satu item dengan skor perhatian."""
    title: str
    score: AttentionScore
    source: str                    # "situation", "work", "protection", "knowledge"
    message: str = ""
    reason: str = ""
    narrative_type: str = ""
    color: str = "#a0a0a0"
    created_at: str = ""


SCORE_COLORS = {
    AttentionScore.IMMEDIATE: "#e06a6a",
    AttentionScore.IMPORTANT: "#e0c06a",
    AttentionScore.NORMAL: "#6aaae0",
    AttentionScore.BACKGROUND: "#606070",
}

SCORE_LABELS = {
    AttentionScore.IMMEDIATE: "Immediate",
    AttentionScore.IMPORTANT: "Important",
    AttentionScore.NORMAL: "Normal",
    AttentionScore.BACKGROUND: "FYI",
}


class AttentionEngine:
    """Menentukan apa yang penting dari Experience Model.

    Home hanya menampilkan TOP 3.
    Sisanya masuk ke Timeline.
    """

    def __init__(self, experience_engine):
        self._ee = experience_engine

    def get_top_items(self, limit: int = 3) -> List[AttentionItem]:
        """Dapatkan item paling penting — TOP N."""
        all_items = self._collect_all()
        sorted_items = sorted(all_items, key=lambda x: x.score, reverse=True)
        return sorted_items[:limit]

    def get_all_scored(self) -> List[AttentionItem]:
        """Dapatkan semua item dengan skor."""
        return sorted(
            self._collect_all(),
            key=lambda x: x.score, reverse=True,
        )

    def _collect_all(self) -> List[AttentionItem]:
        """Kumpulkan semua item dari berbagai sumber."""
        items = []

        try:
            # 1. Situasi
            from .situation import SituationEngine
            sit_engine = SituationEngine(self._ee)
            report = sit_engine.detect()

            sit_score = AttentionScore(report.attention_score) if report.attention_score in (100, 80, 70, 60, 50, 30, 10) else AttentionScore.NORMAL

            items.append(AttentionItem(
                title=report.focus_message,
                score=sit_score,
                source="situation",
                message=report.action_message,
                color=report.color,
            ))

            # Set IMMEDIATE jika action_required
            if report.situation.value in ("action_required", "needs_attention"):
                items[-1] = AttentionItem(
                    title=report.focus_message,
                    score=AttentionScore.IMMEDIATE if report.situation.value == "action_required" else AttentionScore.IMPORTANT,
                    source="situation",
                    message=report.action_message,
                    color=report.color,
                )

            # 2. Work — approval
            work = self._ee.build_work()
            if work and work.items:
                for w in work.items:
                    if w.approval_needed:
                        items.append(AttentionItem(
                            title="Approval needed: {}".format(w.title),
                            score=AttentionScore.IMPORTANT,
                            source="work",
                            message=w.approval_reason or "Review required",
                            narrative_type="approval",
                        ))

                # Running work — NORMAL
                for w in work.items:
                    if w.status == "running":
                        items.append(AttentionItem(
                            title="{} is in progress.".format(w.title),
                            score=AttentionScore.NORMAL,
                            source="work",
                            message="{}% complete".format(w.progress.percent if w.progress else 0),
                            narrative_type="work",
                        ))

            # 3. Protection
            try:
                report = self._ee.protection.get_last_report()
                if report and report.level.value in ("problem", "critical"):
                    items.append(AttentionItem(
                        title=report.summary,
                        score=AttentionScore.IMMEDIATE if report.level.value == "critical" else AttentionScore.IMPORTANT,
                        source="protection",
                        message="{} issue(s) detected".format(len(report.signals)),
                        narrative_type="protection",
                    ))
            except Exception:
                pass

            # 4. Knowledge — rekomendasi
            try:
                knowledge = self._ee.build_knowledge()
                if knowledge and knowledge.items:
                    for k in knowledge.items[:3]:
                        if getattr(k, 'severity', '') == "recommendation":
                            items.append(AttentionItem(
                                title=k.title[:60],
                                score=AttentionScore.NORMAL,
                                source="knowledge",
                                message="Confidence: {:.0f}%".format(k.confidence * 100 if k.confidence else 0),
                                narrative_type="recommendation",
                            ))
            except Exception:
                pass

        except Exception:
            pass

        return items
