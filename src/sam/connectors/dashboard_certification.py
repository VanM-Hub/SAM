"""Dashboard Certification — bridge read-only untuk UI sertifikasi.

Sprint 122 — Connector Certification.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_certification import ConnectorCertifier
from .dashboard_connector import ExecutionCard


class DashboardCertificationBridge:
    """Bridge dashboard certification — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._certifier = ConnectorCertifier(registry)

    def engine_card(self) -> ExecutionCard:
        cert = self._certifier.certify()
        return ExecutionCard(card_id="certification.engine", title="Certification Engine",
                             summary="certified" if cert.certified else "not certified",
                             detail=f"{cert.score} pts", verdict="ok")

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="certification.subsystem", title="Certification Subsystem",
                             summary="score & report", detail="deterministic",
                             verdict="ok")

    def summary_card(self) -> ExecutionCard:
        cert = self._certifier.certify()
        return ExecutionCard(card_id="certification.summary", title="Certification Summary",
                             summary=f"{len(cert.criteria)} criteria",
                             detail=f"score {cert.score}", verdict="ok")

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="certification.detail", title="Certification Detail",
                             summary=f"{self._registry.count()} connectors assessed",
                             detail="manifest v1", verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        cert = self._certifier.certify()
        return ExecutionCard(card_id="certification.verdict", title="Certification Verdict",
                             summary="Universal Connector Runtime certified" if cert.certified
                             else "Universal Connector Runtime ready",
                             detail="Phase XI complete ready", verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
