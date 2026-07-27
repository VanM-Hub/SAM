"""
HumanAnswer — DTO presentasi, bukan domain model.

Domain model sebenarnya adalah ConversationObject.
HumanAnswer hanyalah bentuk presentasi yang sudah dipilih
aspeknya oleh QuestionEngine.

Desktop: render sebagai card
CLI: render sebagai teks
Voice: render sebagai speech
API: render sebagai JSON
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class HumanAnswer:
    """DTO presentasi — bukan domain model.

    Hanya berisi data yang sudah dipilih untuk ditampilkan.
    Tidak ada logika bisnis di sini.
    """
    question: str = ""
    title: str = ""
    summary: str = ""
    details: str = ""
    system_condition: str = ""
    current_activity: str = ""
    user_action_needed: str = ""
    sam_action: str = ""
    attention_label: str = "Normal"
    recommendations: List[str] = field(default_factory=list)
    predictions: List[str] = field(default_factory=list)
    stories: List[str] = field(default_factory=list)
    technical_details: str = ""
    intent: str = ""

    def display_cli(self) -> str:
        """Render untuk CLI."""
        parts = []
        if self.title:
            parts.append(self.title)
        if self.summary and self.summary != self.title:
            parts.append(self.summary)
        if self.sam_action:
            parts.append("")
            parts.append("SAM: {}".format(self.sam_action))
        if self.user_action_needed and \
           self.user_action_needed != "No action required.":
            parts.append("")
            parts.append(self.user_action_needed)
        if self.recommendations:
            parts.append("")
            parts.append("-- Recommendations --")
            for r in self.recommendations:
                parts.append("  {}".format(r))
        if self.predictions:
            parts.append("")
            parts.append("-- Predictions --")
            for p in self.predictions:
                parts.append("  {}".format(p))
        if self.details:
            parts.append("")
            parts.append(self.details)
        if self.technical_details:
            parts.append("")
            parts.append("-- Technical Details --")
            parts.append(self.technical_details)
        return "\n".join(parts)

    def display_short(self) -> str:
        """Render pendek."""
        parts = [self.title]
        if self.user_action_needed and self.user_action_needed != "No action required.":
            parts.append(self.user_action_needed)
        return " -- ".join(parts)


# ============================================================================
# Renderer — ConversationObject → HumanAnswer
# ============================================================================

from .conversation import ConversationObject


class DesktopRenderer:
    """ConversationObject → HumanAnswer untuk Desktop dan CLI."""

    def render(self, co: ConversationObject, intent: str = "") -> HumanAnswer:
        """Render ConversationObject untuk intent tertentu."""
        # Pilih bagian berdasarkan intent
        if intent == "overview":
            return self._render_overview(co)
        elif intent == "health":
            return self._render_health(co)
        elif intent == "user_action":
            return self._render_user_action(co)
        elif intent == "explain":
            return self._render_explain(co)
        elif intent == "changes":
            return self._render_changes(co)
        elif intent == "next_step":
            return self._render_next_step(co)
        elif intent == "consequence":
            return self._render_consequence(co)
        elif intent == "technical":
            return self._render_technical(co)
        else:
            return self._render_overview(co)

    def _render_overview(self, co: ConversationObject) -> HumanAnswer:
        return HumanAnswer(
            title=co.mission_condition,
            summary=co.mission_activity,
            user_action_needed=co.user_action_needed,
            sam_action=co.sam_action,
            attention_label=co.attention_label,
            recommendations=co.recommendations[:2],
            predictions=co.predictions[:1],
            stories=co.activity_changes[:3],
            technical_details=co.technical_details,
        )

    def _render_health(self, co: ConversationObject) -> HumanAnswer:
        if co.situation_severity in ("information",):
            return HumanAnswer(
                title="Everything is operating normally.",
                summary="No issues detected. Monitoring continues.",
                user_action_needed="No action required.",
                attention_label="Normal",
            )
        return HumanAnswer(
            title=co.mission_condition,
            summary=co.mission_activity,
            user_action_needed=co.user_action_needed,
            attention_label=co.attention_label,
        )

    def _render_user_action(self, co: ConversationObject) -> HumanAnswer:
        return HumanAnswer(
            title=co.user_action_needed,
            summary=co.mission_activity,
            recommendations=co.recommendations[:3],
            attention_label=co.attention_label,
        )

    def _render_explain(self, co: ConversationObject) -> HumanAnswer:
        lines = co.evidence[:3] if co.evidence else ["No specific reason found."]
        if co.facts:
            lines = co.facts[:2] + lines
        summary = " ".join(lines[:3])
        return HumanAnswer(
            title=summary[:120] if summary else "No specific reason found.",
            summary=summary,
            details="Check Activities for more context.",
            technical_details=co.technical_details,
        )

    def _render_changes(self, co: ConversationObject) -> HumanAnswer:
        if co.activity_changes:
            return HumanAnswer(
                title="Recent changes." if len(co.activity_changes) > 1 else co.activity_changes[0],
                summary="\n".join(co.activity_changes),
                stories=co.activity_changes,
            )
        else:
            return HumanAnswer(
                title="Nothing significant has changed.",
                summary="Everything is operating normally.",
            )

    def _render_next_step(self, co: ConversationObject) -> HumanAnswer:
        if co.recommendations:
            return HumanAnswer(
                title="Recommendation available.",
                summary=co.recommendations[0],
                recommendations=co.recommendations,
                predictions=co.predictions[:1],
            )
        else:
            return HumanAnswer(
                title="No specific recommendation.",
                summary="Everything is operating normally. Continue monitoring.",
            )

    def _render_consequence(self, co: ConversationObject) -> HumanAnswer:
        if co.risks:
            return HumanAnswer(
                title=co.risks[0],
                summary=co.predictions[0] if co.predictions else co.risks[0],
                predictions=co.predictions,
                recommendations=co.recommendations[:2],
            )
        else:
            return HumanAnswer(
                title="No negative impact expected.",
                summary="Everything is operating normally.",
            )

    def _render_technical(self, co: ConversationObject) -> HumanAnswer:
        return HumanAnswer(
            title=co.mission_condition,
            details=co.technical_details or "No technical details available.",
            technical_details=co.technical_details,
            attention_label=co.attention_label,
        )
