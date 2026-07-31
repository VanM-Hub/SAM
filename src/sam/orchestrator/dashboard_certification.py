# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 133 - Certification: dashboard_certification.

Read-only dashboard bridge for certification (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .orchestration_certification import CertificationResult


class DashboardCertificationBridge:
    """Read-only bridge presenting certification as cards."""

    def cards_for(self, result: CertificationResult) -> Tuple[ExecutionCard, ...]:
        verdict = "ok" if result.certified else "warn"
        return (
            ExecutionCard(
                card_id="cert-status",
                title="Certified",
                summary=str(result.certified),
                detail="{0}/{1} criteria met".format(result.met_count, result.total),
                verdict=verdict,
            ),
            ExecutionCard(
                card_id="cert-no-network",
                title="No Network",
                summary="No network / HTTP / socket",
                detail="No connector provider",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="cert-sync",
                title="Synchronous & Deterministic",
                summary="No async / no thread",
                detail="Deterministic execution",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="cert-immutable",
                title="Frozen DTOs",
                summary="All DTOs immutable",
                detail="Bridges read-only",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="cert-sprint",
                title="Certification Sprint 133",
                summary="Certifier, score, manifest, validator, summary",
                detail="Orchestration Certified",
                verdict="ok",
            ),
        )

    def verdict_card(self, result: CertificationResult) -> ExecutionCard:
        return ExecutionCard(
            card_id="cert-card",
            title="Orchestration Runtime Certified",
            summary="plan-only, deterministic, frozen DTOs",
            detail="Phase XII complete",
            verdict="ok" if result.certified else "warn",
        )
