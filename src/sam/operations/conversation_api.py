"""
Conversation — Public API untuk semua interaksi manusia.

Desktop, CLI, Voice, API — semuanya lewat sini.
Tidak ada yang tahu engine di baliknya.

sam.observe() -> Conversation
    .answer("What's happening?")
    .timeline()
    .recommendations()
    .predictions()
    .technical_details()
    .export_json()
    .story()
"""

from typing import Optional, List

from .human_answer import HumanAnswer
from .conversation import ConversationObject
from .conversation_context import ConversationContext
from .intent import InteractionIntent
from .intent_resolver import IntentResolver
from .understanding import UnderstandingEngine
from .audience import AudienceProfile, get_profile, AudienceType
from .session import MissionSession, SessionManager
from ..render import CLIRenderer, DesktopRenderer, JSONRenderer


INTENT_MAP = {
    "overview": InteractionIntent.OVERVIEW,
    "health": InteractionIntent.HEALTH,
    "user_action": InteractionIntent.USER_ACTION,
    "explain": InteractionIntent.EXPLAIN,
    "changes": InteractionIntent.CHANGES,
    "next_step": InteractionIntent.NEXT_STEP,
    "consequence": InteractionIntent.CONSEQUENCE,
    "technical": InteractionIntent.TECHNICAL,
}


class Conversation:
    """Satu percakapan — hasil dari sam.observe().

    Semua interaksi pengguna terjadi melalui objek ini.
    Pengguna tidak tahu ada engine, resolver, renderer di belakangnya.
    """

    def __init__(self, understanding: 'SystemAnalyzer',
                 session: SessionManager,
                 audience: AudienceProfile,
                 renderers: dict):
        self._understanding = understanding
        self._session = session
        self._audience = audience
        self._renderers = renderers
        self._context = ConversationContext()

        # Dapatkan ConversationObject saat init
        self._co = understanding.understand()

    # ==================================================================
    # Jawaban pertanyaan
    # ==================================================================

    def answer(self, question: str = "",
               audience_type: str = "") -> HumanAnswer:
        """Jawab pertanyaan manusia."""
        if audience_type:
            self._audience = get_profile(audience_type)
            self._session.set_audience(audience_type)

        return self._answer_text(question)

    def _answer_text(self, question: str) -> HumanAnswer:
        intent = IntentResolver.resolve(question)
        self._co = self._understanding.understand()
        answer = self._render_for_intent(intent)
        answer.question = question
        answer.intent = intent.value
        self._session.record_interaction(question, intent, answer)
        return answer

    # ==================================================================
    # Intent-specific methods
    # ==================================================================

    def timeline(self) -> HumanAnswer:
        """Aktivitas terbaru."""
        return self._answer_intent(InteractionIntent.CHANGES)

    def story(self) -> HumanAnswer:
        """Cerita operasional."""
        return self._answer_intent(InteractionIntent.OVERVIEW)

    def recommendations(self) -> HumanAnswer:
        """Apa yang harus dilakukan selanjutnya."""
        return self._answer_intent(InteractionIntent.NEXT_STEP)

    def predictions(self) -> HumanAnswer:
        """Apa yang terjadi jika tidak ada tindakan."""
        return self._answer_intent(InteractionIntent.CONSEQUENCE)

    def technical_details(self) -> HumanAnswer:
        """Detail teknis."""
        return self._answer_intent(InteractionIntent.TECHNICAL)

    def health(self) -> HumanAnswer:
        """Apakah semuanya baik-baik saja."""
        return self._answer_intent(InteractionIntent.HEALTH)

    def actions(self) -> HumanAnswer:
        """Tindakan yang perlu dilakukan."""
        return self._answer_intent(InteractionIntent.USER_ACTION)

    def explain(self) -> HumanAnswer:
        """Kenapa ini terjadi."""
        return self._answer_intent(InteractionIntent.EXPLAIN)

    # ==================================================================
    # Render
    # ==================================================================

    def render_cli(self, answer: HumanAnswer) -> str:
        return self._renderers["cli"].render(answer)

    def render_desktop(self, answer: HumanAnswer) -> dict:
        return self._renderers["desktop"].render(answer)

    def export_json(self, answer: Optional[HumanAnswer] = None) -> dict:
        ans = answer or self._render_for_intent(InteractionIntent.OVERVIEW)
        return self._renderers["json"].render(ans)

    # ==================================================================
    # Internal
    # ==================================================================

    def _answer_intent(self, intent: InteractionIntent) -> HumanAnswer:
        self._co = self._understanding.understand()
        answer = self._render_for_intent(intent)
        answer.intent = intent.value
        return answer

    def _render_for_intent(self, intent: InteractionIntent) -> HumanAnswer:
        iv = intent.value
        # Delegasi ke internal renderer
        if iv == "overview":
            return self._render_overview()
        elif iv == "health":
            return self._render_health()
        elif iv == "user_action":
            return self._render_user_action()
        elif iv == "explain":
            return self._render_explain()
        elif iv == "changes":
            return self._render_changes()
        elif iv == "next_step":
            return self._render_next_step()
        elif iv == "consequence":
            return self._render_consequence()
        elif iv == "technical":
            return self._render_technical()
        return self._render_overview()

    def _render_overview(self) -> HumanAnswer:
        co, p = self._co, self._audience
        sections, cards, actions = [], [], []
        if p.technical_level >= 2 and co.activity_changes:
            sections.append(("Recent Changes", "\n".join(co.activity_changes[:3])))
        if co.user_action_needed and "No action" not in co.user_action_needed:
            actions.append(co.user_action_needed)
        if co.recommendations and p.verbosity != "brief":
            sections.append(("Recommendations", "\n".join(co.recommendations)))
        if co.predictions and p.show_predictions:
            sections.append(("Predictions", "\n".join(co.predictions)))
        if co.sam_action:
            cards.append(("\u2699", "SAM", co.sam_action))
        if p.show_evidence and co.evidence:
            sections.append(("Evidence", "\n".join(co.evidence[:2])))
        icons = {"critical": "\U0001f6a8", "action_required": "\u26a0", "attention": "\u26a0", "information": "\u2705"}
        return HumanAnswer(title=co.mission_condition, summary=co.mission_activity,
                           sections=sections, cards=cards, actions=actions,
                           severity=co.situation_severity,
                           priority=1 if co.situation_severity in ("critical", "action_required") else 3,
                           icon=icons.get(co.situation_severity, "\u2705"),
                           badges=[(p.label, "#505060")])

    def _render_health(self) -> HumanAnswer:
        if self._co.situation_severity in ("information",):
            return HumanAnswer(title="Everything is operating normally.",
                               summary="No issues detected. Monitoring continues.",
                               severity="success", icon="\u2705",
                               badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title=self._co.mission_condition, summary=self._co.mission_activity,
                           severity=self._co.situation_severity, icon="\u26a0",
                           badges=[(self._audience.label, "#505060")])

    def _render_user_action(self) -> HumanAnswer:
        acts = []
        if self._co.user_action_needed and "No action" not in self._co.user_action_needed:
            acts.append(self._co.user_action_needed)
        acts.extend(self._co.recommendations[:3])
        return HumanAnswer(title=self._co.user_action_needed, summary=self._co.mission_activity,
                           actions=acts, severity=self._co.situation_severity,
                           icon="\u2757", badges=[(self._audience.label, "#505060")])

    def _render_explain(self) -> HumanAnswer:
        sections = []
        if self._audience.show_evidence and self._co.evidence:
            sections.append(("Evidence", "\n".join(self._co.evidence[:3])))
        if self._co.facts:
            sections.append(("Facts", "\n".join(self._co.facts[:2])))
        summary = self._co.evidence[0] if self._co.evidence else "No specific reason found."
        return HumanAnswer(title=summary[:120], summary=summary, sections=sections,
                           severity=self._co.situation_severity, icon="\u2753",
                           badges=[(self._audience.label, "#505060")])

    def _render_changes(self) -> HumanAnswer:
        if self._co.activity_changes:
            s = "\n".join(self._co.activity_changes)
            return HumanAnswer(title="Recent changes." if len(self._co.activity_changes) > 1 else self._co.activity_changes[0],
                               summary=s, sections=[("Changes", s)],
                               icon="\U0001f504", badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title="Nothing significant has changed.", summary="Everything is operating normally.",
                           icon="\u2705", badges=[(self._audience.label, "#505060")])

    def _render_next_step(self) -> HumanAnswer:
        if self._co.recommendations:
            return HumanAnswer(title="Recommendation available.", summary=self._co.recommendations[0],
                               sections=[("Recommendations", "\n".join(self._co.recommendations))],
                               predictions=self._co.predictions[:1], icon="\U0001f4a1",
                               badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title="No specific recommendation.", summary="Everything is operating normally.",
                           icon="\u2705", badges=[(self._audience.label, "#505060")])

    def _render_consequence(self) -> HumanAnswer:
        if self._co.risks:
            return HumanAnswer(title=self._co.risks[0],
                               summary=self._co.predictions[0] if self._co.predictions else self._co.risks[0],
                               sections=[("Risks", "\n".join(self._co.risks))],
                               predictions=self._co.predictions, actions=self._co.recommendations[:2],
                               icon="\U0001f52e", badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title="No negative impact expected.", summary="Everything is operating normally.",
                           icon="\u2705", badges=[(self._audience.label, "#505060")])

    def _render_technical(self) -> HumanAnswer:
        return HumanAnswer(title=self._co.mission_condition,
                           details=self._co.technical_details or "No technical details available.",
                           sections=[("Technical", self._co.technical_details)] if self._co.technical_details else [],
                           icon="\u2699", badges=[(self._audience.label, "#505060")])


class SAM:
    """Entry point publik — satu-satunya cara berinteraksi dengan SAM.

    sam = SAM()
    conversation = sam.observe()
    answer = conversation.answer("What's happening?")
    """

    def __init__(self, experience_engine=None):
        self._ee = experience_engine
        self._understanding = SystemAnalyzer(experience_engine)
        self._session = SessionManager()
        self._renderers = {
            "cli": CLIRenderer(),
            "desktop": DesktopRenderer(),
            "json": JSONRenderer(),
        }

    def observe(self, audience_type: str = AudienceType.ADMINISTRATOR,
                mission_target: str = "Workspace") -> Conversation:
        """Mulai percakapan — amati keadaan sistem.

        Ini adalah satu-satunya cara memulai.
        Tidak ada engine, resolver, renderer yang terlihat.
        """
        profile = get_profile(audience_type)
        self._session.start_session(audience_type, mission_target)
        return Conversation(
            understanding=self._understanding,
            session=self._session,
            audience=profile,
            renderers=self._renderers,
        )
