"""
Question Engine — Conversation-first Operations.

Pipeline FINAL:
ConversationObject
     ↓
AudienceProfile (siapa yang mendengar)
     ↓
QuestionIntent (aspek mana)
     ↓
Renderer (bagaimana menyampaikan)
     ↓
HumanAnswer (DTO murni)

Semua dari ConversationObject.
Tidak ada builder paralel.
Tidak ada logika naratif terpisah.
"""

from typing import Optional

from .human_answer import HumanAnswer
from .conversation import ConversationObject
from .conversation_context import ConversationContext
from .intent import QuestionIntent
from .intent_resolver import IntentResolver
from .understanding import UnderstandingEngine
from .audience import AudienceProfile, get_profile, AudienceType
from .session import MissionSession, SessionManager
from ..render import CLIRenderer, DesktopRenderer, JSONRenderer


class QuestionEngine:
    """Question Engine — Audience + Intent → Render → HumanAnswer.

    BUKAN NLP. BUKAN AI.
    Hanya routing: ConversationObject + Audience + Intent → Renderer.
    """

    def __init__(self, experience_engine=None):
        self.understanding = UnderstandingEngine(experience_engine)
        self.session = SessionManager()
        self.renderers = {
            "cli": CLIRenderer(),
            "desktop": DesktopRenderer(),
            "json": JSONRenderer(),
        }

    def answer(self, question: str = "",
               context: Optional[ConversationContext] = None,
               audience_type: str = "",
               render_format: str = "cli") -> HumanAnswer:
        """Jawab pertanyaan manusia — dengan audiens.

        Pipeline:
        question → Intent → ConversationObject → Audience → Renderer → HumanAnswer
        """
        # 1. Set audiens (jika diberikan)
        if audience_type:
            self.session.set_audience(audience_type)

        # 2. Resolve intent
        intent = IntentResolver.resolve(question)

        # 3. Satu ConversationObject — sumber kebenaran
        co = self.understanding.understand()

        # 4. Render
        answer = self._render(co, intent.value, self.session.session.audience)

        # 5. Metadata
        answer.question = question
        answer.intent = intent.value

        # 6. Simpan interaksi
        self.session.record_interaction(question, intent, answer)

        return answer

    # ======================================================================
    # Internal
    # ======================================================================

    def _render(self, co: ConversationObject, intent: str,
                profile: AudienceProfile) -> HumanAnswer:
        """Render ConversationObject → HumanAnswer dengan audiens."""

        # Pilih aspek berdasarkan intent
        if intent == "overview":
            return self._render_overview(co, profile)
        elif intent == "health":
            return self._render_health(co, profile)
        elif intent == "user_action":
            return self._render_user_action(co, profile)
        elif intent == "explain":
            return self._render_explain(co, profile)
        elif intent == "changes":
            return self._render_changes(co, profile)
        elif intent == "next_step":
            return self._render_next_step(co, profile)
        elif intent == "consequence":
            return self._render_consequence(co, profile)
        elif intent == "technical":
            return self._render_technical(co, profile)
        else:
            return self._render_overview(co, profile)

    def _render_overview(self, co: ConversationObject,
                         profile: AudienceProfile) -> HumanAnswer:
        sections = []
        cards = []
        actions = []
        severity = co.situation_severity

        # Kondisi utama
        title = co.mission_condition
        summary = co.mission_activity

        # Progress — untuk Developer
        if profile.technical_level >= 2 and co.activity_changes:
            sections.append(("Recent Changes", "\n".join(co.activity_changes[:3])))

        # Actions
        if co.user_action_needed and "No action" not in co.user_action_needed:
            actions.append(co.user_action_needed)

        # Recommendations — tergantung preferensi
        if co.recommendations and profile.verbosity != "brief":
            sections.append(("Recommendations", "\n".join(co.recommendations)))

        # Predictions
        if co.predictions and profile.show_predictions:
            sections.append(("Predictions", "\n".join(co.predictions)))

        # SAM action (hanya jika SAM bertindak)
        if co.sam_action:
            cards.append(("\u2699\ufe0f", "SAM", co.sam_action))

        # Evidence — untuk Developer
        if profile.show_evidence and co.evidence:
            sections.append(("Evidence", "\n".join(co.evidence[:2])))

        icon_map = {
            "critical": "\U0001f6a8",
            "action_required": "\u26a0\ufe0f",
            "attention": "\u26a0\ufe0f",
            "information": "\u2705",
        }
        icon = icon_map.get(severity, "\u2705")

        return HumanAnswer(
            title=title,
            summary=summary,
            sections=sections,
            cards=cards,
            actions=actions,
            severity=severity,
            priority=1 if severity in ("critical", "action_required") else 3,
            icon=icon,
            badges=[(profile.label, "#505060")],
        )

    def _render_health(self, co: ConversationObject,
                       profile: AudienceProfile) -> HumanAnswer:
        if co.situation_severity in ("information",):
            return HumanAnswer(
                title="Everything is operating normally.",
                summary="No issues detected. Monitoring continues.",
                severity="success",
                icon="\u2705",
                badges=[(profile.label, "#505060")],
            )
        return HumanAnswer(
            title=co.mission_condition,
            summary=co.mission_activity,
            severity=co.situation_severity,
            icon="\u26a0\ufe0f",
            badges=[(profile.label, "#505060")],
        )

    def _render_user_action(self, co: ConversationObject,
                            profile: AudienceProfile) -> HumanAnswer:
        actions = []
        if co.user_action_needed and "No action" not in co.user_action_needed:
            actions.append(co.user_action_needed)
        if co.recommendations:
            actions.extend(co.recommendations[:3])

        return HumanAnswer(
            title=co.user_action_needed,
            summary=co.mission_activity,
            actions=actions,
            severity=co.situation_severity,
            icon="\u2757",
            badges=[(profile.label, "#505060")],
        )

    def _render_explain(self, co: ConversationObject,
                        profile: AudienceProfile) -> HumanAnswer:
        sections = []

        # Evidence — tergantung audiens
        if profile.show_evidence and co.evidence:
            sections.append(("Evidence", "\n".join(co.evidence[:3])))

        # Facts
        if co.facts:
            sections.append(("Facts", "\n".join(co.facts[:2])))

        summary = co.evidence[0] if co.evidence else "No specific reason found."
        title = summary[:120]

        return HumanAnswer(
            title=title,
            summary=summary,
            sections=sections,
            severity=co.situation_severity,
            icon="\u2753",
            badges=[(profile.label, "#505060")],
        )

    def _render_changes(self, co: ConversationObject,
                        profile: AudienceProfile) -> HumanAnswer:
        if co.activity_changes:
            summary = "\n".join(co.activity_changes)
            return HumanAnswer(
                title="Recent changes." if len(co.activity_changes) > 1 else co.activity_changes[0],
                summary=summary,
                sections=[("Changes", summary)],
                icon="\U0001f504",
                badges=[(profile.label, "#505060")],
            )
        return HumanAnswer(
            title="Nothing significant has changed.",
            summary="Everything is operating normally.",
            icon="\u2705",
            badges=[(profile.label, "#505060")],
        )

    def _render_next_step(self, co: ConversationObject,
                          profile: AudienceProfile) -> HumanAnswer:
        if co.recommendations:
            return HumanAnswer(
                title="Recommendation available.",
                summary=co.recommendations[0],
                sections=[("Recommendations", "\n".join(co.recommendations))],
                predictions=co.predictions[:1],
                icon="\U0001f4a1",
                badges=[(profile.label, "#505060")],
            )
        return HumanAnswer(
            title="No specific recommendation.",
            summary="Everything is operating normally.",
            icon="\u2705",
            badges=[(profile.label, "#505060")],
        )

    def _render_consequence(self, co: ConversationObject,
                            profile: AudienceProfile) -> HumanAnswer:
        if co.risks:
            return HumanAnswer(
                title=co.risks[0],
                summary=co.predictions[0] if co.predictions else co.risks[0],
                sections=[("Risks", "\n".join(co.risks))],
                predictions=co.predictions,
                actions=co.recommendations[:2],
                icon="\U0001f52e",
                badges=[(profile.label, "#505060")],
            )
        return HumanAnswer(
            title="No negative impact expected.",
            summary="Everything is operating normally.",
            icon="\u2705",
            badges=[(profile.label, "#505060")],
        )

    def _render_technical(self, co: ConversationObject,
                          profile: AudienceProfile) -> HumanAnswer:
        return HumanAnswer(
            title=co.mission_condition,
            details=co.technical_details or "No technical details available.",
            sections=[("Technical", co.technical_details)] if co.technical_details else [],
            icon="\u2699\ufe0f",
            badges=[(profile.label, "#505060")],
        )

    # ======================================================================
    # Format helpers — backward compat
    # ======================================================================

    def render_for_cli(self, answer: HumanAnswer) -> str:
        """Render HumanAnswer sebagai teks CLI."""
        return self.renderers["cli"].render(answer)

    def render_for_desktop(self, answer: HumanAnswer) -> dict:
        """Render HumanAnswer sebagai dict untuk Desktop."""
        return self.renderers["desktop"].render(answer)

    def render_for_json(self, answer: HumanAnswer) -> dict:
        """Render HumanAnswer sebagai JSON."""
        return self.renderers["json"].render(answer)
