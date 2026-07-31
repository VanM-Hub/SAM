"""Dashboard Translation — bridge read-only untuk UI terjemahan.

Sprint 118 — Connector Translation.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .dashboard_connector import ExecutionCard


class DashboardTranslationBridge:
    """Bridge dashboard translation — 5 ExecutionCard."""

    def __init__(self) -> None:
        pass

    def engine_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="translation.engine", title="Translation Engine",
                             summary="internal -> neutral DTO", detail="schema sam.neutral.v1",
                             verdict="ok")

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="translation.subsystem", title="Translation Subsystem",
                             summary="provider-agnostic", detail="no provider format yet",
                             verdict="ok")

    def summary_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="translation.summary", title="Translation Summary",
                             summary="neutral translation ready", detail="deterministic",
                             verdict="ok")

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="translation.detail", title="Translation Detail",
                             summary="internal -> neutral mapping", detail="read-only",
                             verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="translation.verdict", title="Translation Verdict",
                             summary="Translation ready", detail="Ready for preview",
                             verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
