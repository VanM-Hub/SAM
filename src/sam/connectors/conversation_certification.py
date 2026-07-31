"""Conversation Certification — bridge read-only untuk sertifikasi.

Sprint 122 — Connector Certification.
Query read-only ke certifier/scorer/reporter. Tidak ada mutasi.
"""
from __future__ import annotations

from .connector_registry import ConnectorRegistry
from .connector_certification import ConnectorCertifier, CertificationResult
from .connector_score import ConnectorScore, ConnectorScorer
from .connector_report import ConnectorReport, ConnectorReporter


class ConversationCertificationBridge:
    """Bridge conversation certification — read-only."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._certifier = ConnectorCertifier(registry)
        self._scorer = ConnectorScorer(registry)
        self._reporter = ConnectorReporter()

    def certify(self) -> CertificationResult:
        return self._certifier.certify()

    def score(self, connector_id: str) -> ConnectorScore:
        return self._scorer.score(connector_id)

    def report(self) -> ConnectorReport:
        return self._reporter.report(self._certifier.certify())
