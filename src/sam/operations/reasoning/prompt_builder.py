"""
OP-283 — Prompt Builder

Membangun PromptContext dari data SAM (DTOs saja).
Tidak mengetahui provider — menghasilkan PromptContext murni.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass(frozen=True)
class PromptContext:
    system_prompt: str
    operator_question: str
    conversation_summary: str = ""
    mission_summary: str = ""
    timeline_summary: str = ""
    observation_summary: str = ""
    findings: tuple[dict[str, Any], ...] = ()
    recommendations: tuple[dict[str, Any], ...] = ()
    trust_summary: str = ""
    health_summary: str = ""
    template_name: str = ""
    template_version: str = ""
    evidence_ids: tuple[str, ...] = ()
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_prompt": self.system_prompt,
            "operator_question": self.operator_question,
            "conversation_summary": self.conversation_summary,
            "mission_summary": self.mission_summary,
            "timeline_summary": self.timeline_summary,
            "observation_summary": self.observation_summary,
            "findings": list(self.findings),
            "recommendations": list(self.recommendations),
            "trust_summary": self.trust_summary,
            "health_summary": self.health_summary,
            "template_name": self.template_name,
            "template_version": self.template_version,
            "evidence_ids": list(self.evidence_ids),
            "timestamp": self.timestamp,
        }


class PromptBuilder:
    """
    Membangun PromptContext dari DTO data sources.

    Output pure text — tidak mengandung logika provider.
    """

    def build(self, operator_question: str,
              conversation_summary: str = "",
              mission_summary: str = "",
              timeline_summary: str = "",
              observation_summary: str = "",
              findings: list[dict[str, Any]] | None = None,
              recommendations: list[dict[str, Any]] | None = None,
              trust_summary: str = "",
              health_summary: str = "",
              system_prompt: str = "",
              template_name: str = "",
              template_version: str = "",
              evidence_ids: list[str] | None = None,
              ) -> PromptContext:
        """Build complete PromptContext from parts."""

        return PromptContext(
            system_prompt=system_prompt or "You are SAM's reasoning assistant.",
            operator_question=operator_question,
            conversation_summary=conversation_summary,
            mission_summary=mission_summary,
            timeline_summary=timeline_summary,
            observation_summary=observation_summary,
            findings=tuple(findings or []),
            recommendations=tuple(recommendations or []),
            trust_summary=trust_summary,
            health_summary=health_summary,
            template_name=template_name,
            template_version=template_version,
            evidence_ids=tuple(evidence_ids or []),
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def build_minimal(self, operator_question: str) -> PromptContext:
        """Build minimal context (question only)."""
        return self.build(operator_question=operator_question)
