"""
Experience Contract — setiap QuestionIntent memiliki Experience.

Experience menghasilkan HumanAnswer.

BUKAN UI.
BUKAN string mentah.
Experience adalah kontrak: Intent → Answer.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

from .human_answer import HumanAnswer
from .intent import QuestionIntent
from .presentation import Presentation, Decision


# ============================================================================
# ConversationContext — OP-28
# ============================================================================

@dataclass
class ConversationContext:
    """Konteks percakapan — 'Why?' terhadap apa.

    QuestionEngine menerima question + context → jawaban kontekstual.
    """
    selected_work: str = ""
    selected_activity: str = ""
    selected_incident: str = ""
    selected_workspace: str = ""
    current_page: str = "home"
    last_intent: Optional[QuestionIntent] = None
    last_answer: Optional[str] = ""


# ============================================================================
# InteractionMemory — OP-29
# ============================================================================

@dataclass
class InteractionMemory:
    """Memori percakapan — membuat Why? terasa natural tanpa LLM."""
    last_question: str = ""
    last_intent: Optional[QuestionIntent] = None
    last_answer: Optional[HumanAnswer] = None
    last_context: Optional[ConversationContext] = None
    current_page: str = "home"

    def update(self, question: str, intent: QuestionIntent,
               answer: HumanAnswer, context: Optional[ConversationContext] = None):
        self.last_question = question
        self.last_intent = intent
        self.last_answer = answer
        if context:
            self.last_context = context

    def get_context_for_followup(self, question: str) -> ConversationContext:
        """Dapatkan konteks untuk pertanyaan lanjutan.

        Jika user bertanya 'Why?' setelah 'What happened?',
        jawab tentang apa yang baru saja dilaporkan.
        """
        ctx = ConversationContext()
        if self.last_context:
            ctx.current_page = self.last_context.current_page
            ctx.selected_work = self.last_context.selected_work
            ctx.selected_activity = self.last_context.selected_activity
            ctx.selected_incident = self.last_context.selected_incident
            ctx.selected_workspace = self.last_context.selected_workspace
        return ctx


# ============================================================================
# HumanExplainer Protocol — OP-30
# ============================================================================

class HumanExplainer(Protocol):
    """Kontrak: setiap capability WAJIB mengimplementasikan ini.

    Bukan cuma punya fitur.
    Capability tidak dianggap selesai sampai bisa:
    - Memberi overview
    - Menjelaskan kenapa terjadi
    - Merekomendasi langkah selanjutnya
    - Memprediksi konsekuensi
    """

    def overview(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        """Apa yang sedang terjadi? Bagaimana kondisi capability ini?"""
        ...

    def explain(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        """Kenapa ini terjadi? Alasan di balik state saat ini."""
        ...

    def next_step(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        """Apa yang harus dilakukan selanjutnya?"""
        ...

    def prediction(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        """Apa yang akan terjadi jika tidak ada tindakan?"""
        ...


# ============================================================================
# Experience Base Class
# ============================================================================

class BaseExperience:
    """Base untuk semua Experience.

    Setiap Intent punya Experience sendiri.
    Experience hanya membaca PresentationEngine + RecommendationEngine + PredictionEngine.
    TIDAK membaca Runtime.
    """

    def __init__(self, experience_engine=None):
        self.ee = experience_engine

    @property
    def name(self) -> str:
        raise NotImplementedError

    def answer(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        raise NotImplementedError

    # Helpers

    def _get_pres(self):
        if not self.ee:
            return None
        try:
            return self.ee.build_presentation()
        except Exception:
            return None

    def _get_recs(self, limit=3):
        if not self.ee:
            return []
        try:
            return self.ee.get_recommendations(limit=limit)
        except Exception:
            return []

    def _get_preds(self, limit=2):
        if not self.ee:
            return []
        try:
            return self.ee.get_predictions(limit=limit)
        except Exception:
            return []

    def _get_stories(self, limit=5):
        if not self.ee:
            return []
        try:
            return self.ee.build_activity_stories() or []
        except Exception:
            return []


# ============================================================================
# Experience Implementations
# ============================================================================

class OverviewExperience(BaseExperience):
    """Intent: OVERVIEW — 'What's happening?'"""

    @property
    def name(self):
        return "overview"

    def answer(self, context=None):
        pres = self._get_pres()
        recs = self._get_recs(limit=2)
        preds = self._get_preds(limit=1)
        stories = self._get_stories(limit=3)

        condition = pres.system_condition if pres else "Status unknown."
        activity = pres.current_activity if pres else "Monitoring."

        return HumanAnswer(
            question="overview",
            title=condition,
            summary=activity,
            user_action_needed=pres.user_action_needed if pres else "",
            sam_action=pres.sam_action if pres else "",
            attention_label=pres.attention_label if pres else "Normal",
            recommendations=[r.display() for r in recs if r.priority > 10],
            predictions=[p.display() for p in preds if p.risk != "None"],
            stories=[s.title for s in stories],
            technical_details=pres.detail if pres else "",
        )


class HealthExperience(BaseExperience):
    """Intent: HEALTH — 'Is everything okay?'"""

    @property
    def name(self):
        return "health"

    def answer(self, context=None):
        pres = self._get_pres()
        condition = pres.system_condition if pres else "Status unknown."

        if "normal" in condition.lower() or "healthy" in condition.lower():
            return HumanAnswer(
                question="health",
                title="Everything is operating normally.",
                summary="No issues detected. Monitoring continues.",
                user_action_needed="No action required.",
                attention_label="Normal",
            )
        else:
            return HumanAnswer(
                question="health",
                title=condition,
                summary="Attention may be required.",
                user_action_needed=pres.user_action_needed if pres else "Check overview.",
                attention_label=pres.attention_label if pres else "Normal",
            )


class UserActionExperience(BaseExperience):
    """Intent: USER_ACTION — 'Do I need to do anything?'"""

    @property
    def name(self):
        return "user_action"

    def answer(self, context=None):
        pres = self._get_pres()
        recs = self._get_recs(limit=3)

        needed = pres.user_action_needed if pres else "No action required."
        return HumanAnswer(
            question="user_action",
            title=needed,
            summary=pres.current_activity if pres else "",
            recommendations=[r.display() for r in recs if r.priority > 10],
            attention_label=pres.attention_label if pres else "Normal",
        )


class ExplainExperience(BaseExperience):
    """Intent: EXPLAIN — 'Why?' Dengan ConversationContext."""

    @property
    def name(self):
        return "explain"

    def answer(self, context=None):
        """Jawab 'Why?' — kontekstual berdasarkan ConversationContext."""
        if not self.ee:
            return HumanAnswer(
                question="explain",
                title="No explanation available.",
                summary="The system does not have enough information.",
            )
        try:
            situation = None
            if hasattr(self.ee, 'situation'):
                situation = self.ee.situation.detect()
            
            # Gunakan konteks
            target = ""
            if context:
                if context.selected_work:
                    target = context.selected_work
                elif context.selected_activity:
                    target = context.selected_activity
                elif context.selected_incident:
                    target = context.selected_incident

            reasons = []
            if target:
                reasons.append("Regarding {}.".format(target))
            if situation:
                reasons.append("Current situation: {}.".format(situation.situation.value))
                if hasattr(situation, 'reason') and situation.reason:
                    reasons.append(situation.reason)

            summary = " ".join(reasons[:3]) if reasons else "Current situation: {}.".format(situation.situation.value) if situation else "No specific reason found."

            return HumanAnswer(
                question="explain",
                title=summary[:120] if summary else "No specific reason found.",
                summary=summary,
                details="Check Work or Activity for more context." if not target else "",
                technical_details="Situation: {}".format(
                    situation.situation.value if situation else "unknown"
                ),
            )
        except Exception as e:
            return HumanAnswer(
                question="explain",
                title="Explain: {}".format(str(e)[:100]),
                summary=str(e)[:200],
            )


class ChangesExperience(BaseExperience):
    """Intent: CHANGES — 'What changed?'"""

    @property
    def name(self):
        return "changes"

    def answer(self, context=None):
        stories = self._get_stories(limit=5)
        if stories:
            titles = [s.title for s in stories]
            return HumanAnswer(
                question="changes",
                title="Recent changes detected." if len(titles) > 1 else titles[0],
                summary="\n".join(titles),
                stories=titles,
            )
        else:
            return HumanAnswer(
                question="changes",
                title="Nothing significant has changed.",
                summary="Everything is operating normally.",
            )


class NextStepExperience(BaseExperience):
    """Intent: NEXT_STEP — 'What should happen next?'"""

    @property
    def name(self):
        return "next_step"

    def answer(self, context=None):
        recs = self._get_recs(limit=3)
        valid = [r for r in recs if r.priority > 10]

        if valid:
            return HumanAnswer(
                question="next_step",
                title="Recommendation available.",
                summary=valid[0].display(),
                recommendations=[r.display() for r in valid],
                predictions=[p.display() for p in self._get_preds(limit=1)],
            )
        else:
            return HumanAnswer(
                question="next_step",
                title="No specific recommendation.",
                summary="Everything is operating normally. Continue monitoring.",
            )


class ConsequenceExperience(BaseExperience):
    """Intent: CONSEQUENCE — 'What happens if nothing is done?'"""

    @property
    def name(self):
        return "consequence"

    def answer(self, context=None):
        preds = self._get_preds(limit=2)
        valid = [p for p in preds if p.risk != "None"]

        if valid:
            return HumanAnswer(
                question="consequence",
                title=valid[0].display(),
                summary=valid[0].impact,
                predictions=[p.display() for p in valid],
                recommendations=[r.display() for r in self._get_recs(limit=2) if r.priority > 10],
            )
        else:
            return HumanAnswer(
                question="consequence",
                title="No negative impact expected.",
                summary="Everything is operating normally.",
            )


class TechnicalExperience(BaseExperience):
    """Intent: TECHNICAL — 'Show technical details.'"""

    @property
    def name(self):
        return "technical"

    def answer(self, context=None):
        pres = self._get_pres()
        return HumanAnswer(
            question="technical",
            title=pres.system_condition if pres else "",
            details=pres.detail if pres else "No technical details available.",
            technical_details=pres.detail if pres else "",
            attention_label=pres.attention_label if pres else "Normal",
        )


# ============================================================================
# Registry — Intent → Experience
# ============================================================================

INTENT_EXPERIENCE = {
    QuestionIntent.OVERVIEW: OverviewExperience,
    QuestionIntent.HEALTH: HealthExperience,
    QuestionIntent.USER_ACTION: UserActionExperience,
    QuestionIntent.EXPLAIN: ExplainExperience,
    QuestionIntent.CHANGES: ChangesExperience,
    QuestionIntent.NEXT_STEP: NextStepExperience,
    QuestionIntent.CONSEQUENCE: ConsequenceExperience,
    QuestionIntent.TECHNICAL: TechnicalExperience,
}


def get_experience(intent: QuestionIntent, ee=None) -> BaseExperience:
    """Dapatkan Experience untuk Intent tertentu."""
    cls = INTENT_EXPERIENCE.get(intent)
    if not cls:
        cls = OverviewExperience
    return cls(ee)
