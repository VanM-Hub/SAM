"""
Question Engine — Conversation-first Operations.

Question Engine adalah SINGLE SOURCE untuk semua User-Facing Language.
BUKAN Narrative Engine.

Narrative Engine menghasilkan cerita.
Question Engine menghasilkan jawaban.

Desktop, CLI, Assistant, Future Voice, Future API
→ semua lewat sini.

TIDAK membaca Runtime.
HANYA membaca PresentationEngine, RecommendationEngine,
PredictionEngine, SituationEngine, Experience Models.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HumanAnswer:
    """Jawaban untuk manusia — model tunggal untuk semua UI.

    Desktop: render sebagai card
    CLI: render sebagai teks
    Voice: render sebagai speech
    API: render sebagai JSON
    """
    question: str = ""
    title: str = ""                 # "Workspace operating normally."
    summary: str = ""               # "Monitoring continues."
    details: str = ""               # Level 2 — teknis
    system_condition: str = ""      # "Operating normally."
    current_activity: str = ""      # "Monitoring continues."
    user_action_needed: str = ""    # "No action required."
    sam_action: str = ""            # Hanya jika SAM bertindak
    attention_label: str = "Normal"

    # Dari RecommendationEngine
    recommendations: List[str] = field(default_factory=list)

    # Dari PredictionEngine
    predictions: List[str] = field(default_factory=list)

    # Story — apa yang baru saja berubah
    stories: List[str] = field(default_factory=list)

    # Level 2 — teknis
    technical_details: str = ""

    def display_cli(self) -> str:
        """Render untuk CLI — teks sederhana."""
        lines = []
        if self.title:
            lines.append(self.title)
        if self.summary:
            lines.append(self.summary)
        if self.sam_action:
            lines.append("")
            lines.append("SAM: {}".format(self.sam_action))
        if self.user_action_needed:
            lines.append("")
            lines.append(self.user_action_needed)
        if self.recommendations:
            lines.append("")
            lines.append("-- Recommendations --")
            for r in self.recommendations:
                lines.append("  {}".format(r))
        if self.predictions:
            lines.append("")
            lines.append("-- Predictions --")
            for p in self.predictions:
                lines.append("  {}".format(p))
        if self.details:
            lines.append("")
            lines.append(self.details)
        if self.technical_details:
            lines.append("")
            lines.append("-- Technical Details --")
            lines.append(self.technical_details)
        return "\n".join(lines)

    def display_short(self) -> str:
        """Render pendek — untuk greeting."""
        parts = [self.title]
        if self.user_action_needed and self.user_action_needed != "No action required.":
            parts.append(self.user_action_needed)
        return " — ".join(parts)


# ============================================================================
# Pertanyaan Inti — mapping ke HumanAnswer
# ============================================================================

class QuestionEngine:
    """Menerjemahkan pertanyaan manusia → HumanAnswer.

    BUKAN NLP.
    BUKAN AI.
    Ini adalah mapping deterministik dari pertanyaan ke jawaban.

    Question Engine hanya membaca:
    - PresentationEngine
    - RecommendationEngine
    - PredictionEngine
    - SituationEngine
    - Experience Models
    """

    def __init__(self, experience_engine=None):
        self.ee = experience_engine

    def answer(self, question: str = "") -> HumanAnswer:
        """Jawab pertanyaan manusia.

        Mapping sederhana — keyword-based, bukan NLP.
        """
        if not question or not question.strip():
            return self._answer_happening()

        q = question.strip().lower()

        # Peta pertanyaan → handler
        if any(w in q for w in ["what's happening", "what is happening", "what's going on",
                                "happening", "terjadi", "what happened"]):
            return self._answer_happening()

        if any(w in q for w in ["is everything ok", "is everything okay", "are you ok",
                                "everything ok", "everything okay", "healthy", "sehat",
                                "baik"]):
            return self._answer_everything_ok()

        if any(w in q for w in ["do i need", "do anything", "what should i do",
                                "any action", "action needed", "tindakan", "perlu"]):
            return self._answer_action_needed()

        if q in ("why", "why?", "kenapa", "mengapa"):
            return self._answer_why()

        if any(w in q for w in ["what changed", "what changed?", "perubahan", "berubah"]):
            return self._answer_what_changed()

        if any(w in q for w in ["should happen next", "recommendation", "next step",
                                "rekomendasi", "selanjutnya", "recommend"]):
            return self._answer_what_next()

        if any(w in q for w in ["if i do nothing", "if i ignore", "what happens",
                                "prediksi", "prediction", "nothing"]):
            return self._answer_what_if_nothing()

        if any(w in q for w in ["technical", "detail", "teknis", "rinci"]):
            return self._answer_technical()

        # Fallback: happening
        return self._answer_happening()

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _get_presentation(self):
        """Dapatkan Presentation dari Experience Engine."""
        if not self.ee:
            return None
        try:
            return self.ee.build_presentation()
        except Exception:
            return None

    def _get_recs(self):
        if not self.ee:
            return []
        try:
            return self.ee.get_recommendations(limit=3)
        except Exception:
            return []

    def _get_preds(self):
        if not self.ee:
            return []
        try:
            return self.ee.get_predictions(limit=2)
        except Exception:
            return []

    def _get_stories(self):
        if not self.ee:
            return []
        try:
            return self.ee.build_activity_stories() or []
        except Exception:
            return []

    def _answer_happening(self) -> HumanAnswer:
        """What's happening?"""
        pres = self._get_presentation()
        recs = self._get_recs()
        preds = self._get_preds()
        stories = self._get_stories()

        condition = pres.system_condition if pres else "Status unknown."
        activity = pres.current_activity if pres else "Monitoring."

        return HumanAnswer(
            question="What's happening?",
            title=condition,
            summary=activity,
            user_action_needed=pres.user_action_needed if pres else "",
            sam_action=pres.sam_action if pres else "",
            attention_label=pres.attention_label if pres else "Normal",
            recommendations=[r.display() for r in recs[:2] if r.priority > 10],
            predictions=[p.display() for p in preds[:1] if p.risk != "None"],
            stories=[s.title for s in stories[:3]],
            technical_details=pres.detail if pres else "",
        )

    def _answer_everything_ok(self) -> HumanAnswer:
        """Is everything okay?"""
        pres = self._get_presentation()
        condition = pres.system_condition if pres else "Status unknown."

        if "normal" in condition.lower() or "healthy" in condition.lower():
            return HumanAnswer(
                question="Is everything okay?",
                title="Everything is operating normally.",
                summary="No issues detected. Monitoring continues.",
                user_action_needed="No action required.",
                attention_label="Normal",
            )
        else:
            return HumanAnswer(
                question="Is everything okay?",
                title=condition,
                summary="Attention may be required.",
                user_action_needed=pres.user_action_needed if pres else "Check Home for details.",
                attention_label=pres.attention_label if pres else "Normal",
            )

    def _answer_action_needed(self) -> HumanAnswer:
        """Do I need to do anything?"""
        pres = self._get_presentation()
        recs = self._get_recs()

        needed = pres.user_action_needed if pres else "No action required."
        return HumanAnswer(
            question="Do I need to do anything?",
            title=needed,
            summary=pres.current_activity if pres else "",
            recommendations=[r.display() for r in recs[:3] if r.priority > 10],
            attention_label=pres.attention_label if pres else "Normal",
        )

    def _answer_why(self) -> HumanAnswer:
        """Why?"""
        if not self.ee:
            return HumanAnswer(
                question="Why?",
                title="No explanation available.",
                summary="The system does not have enough information.",
            )
        try:
            home = self.ee.build_home()
            work = self.ee.build_work()
            situation = self.ee.situation.detect() if hasattr(self.ee, 'situation') else None

            reasons = []

            # Situasi
            if situation:
                reasons.append("Current situation: {}.".format(situation.situation.label))
                if situation.reason:
                    reasons.append(situation.reason)

            # Dari work
            if work and work.items:
                for item in work.items[:2]:
                    if hasattr(item, 'reason') and item.reason:
                        reasons.append(item.reason)

            # Dari home
            if home and home.attention and home.attention.message:
                reasons.append(home.attention.message)

            summary = " ".join(reasons[:3]) if reasons else "No specific reason found."

            return HumanAnswer(
                question="Why?",
                title=summary[:120],
                summary=summary,
                details="Check Work or Activity for more context.",
                technical_details="Situation: {}".format(
                    situation.situation.value if situation else "unknown"
                ),
            )
        except Exception:
            return HumanAnswer(
                question="Why?",
                title="Unable to explain.",
                summary="An error occurred while building explanation.",
            )

    def _answer_what_changed(self) -> HumanAnswer:
        """What changed?"""
        stories = self._get_stories()

        if stories:
            titles = [s.title for s in stories[:4]]
            return HumanAnswer(
                question="What changed?",
                title="Recent changes detected." if len(titles) > 1 else titles[0],
                summary="\n".join(titles),
                stories=titles,
            )
        else:
            return HumanAnswer(
                question="What changed?",
                title="Nothing significant has changed.",
                summary="Everything is operating normally.",
            )

    def _answer_what_next(self) -> HumanAnswer:
        """What should happen next?"""
        recs = self._get_recs()
        valid = [r for r in recs if r.priority > 10]

        if valid:
            return HumanAnswer(
                question="What should happen next?",
                title="Recommendation available.",
                summary=valid[0].display(),
                recommendations=[r.display() for r in valid],
                predictions=[p.display() for p in self._get_preds()[:1]],
            )
        else:
            return HumanAnswer(
                question="What should happen next?",
                title="No specific recommendation.",
                summary="Everything is operating normally. Continue monitoring.",
            )

    def _answer_what_if_nothing(self) -> HumanAnswer:
        """What happens if nothing is done?"""
        preds = self._get_preds()
        valid = [p for p in preds if p.risk != "None"]

        if valid:
            return HumanAnswer(
                question="What happens if nothing is done?",
                title=valid[0].display(),
                summary=valid[0].impact,
                predictions=[p.display() for p in valid],
                recommendations=[r.display() for r in self._get_recs()[:2]
                                 if r.priority > 10],
            )
        else:
            return HumanAnswer(
                question="What happens if nothing is done?",
                title="No negative impact expected.",
                summary="Everything is operating normally.",
            )

    def _answer_technical(self) -> HumanAnswer:
        """Show technical details."""
        pres = self._get_presentation()
        return HumanAnswer(
            question="Show technical details.",
            title=pres.system_condition if pres else "",
            details=pres.detail if pres else "No technical details available.",
            technical_details=pres.detail if pres else "",
            attention_label=pres.attention_label if pres else "Normal",
        )
