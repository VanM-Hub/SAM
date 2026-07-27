"""
HumanAnswer — Model tunggal untuk semua UI.

Dipisah dari QuestionEngine untuk menghindari circular import.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class HumanAnswer:
    """Jawaban untuk manusia — model tunggal untuk semua UI.

    Desktop: render sebagai card
    CLI: render sebagai teks
    Voice: render sebagai speech
    API: render sebagai JSON
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

    # Metadata
    intent: str = ""

    def display_cli(self) -> str:
        """Render untuk CLI — teks sederhana."""
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
