# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 143 - Mission Certification: dashboard_certification.

Read-only dashboard bridge for certification (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .mission_certification import CertificationResult


class DashboardCertificationBridge:
    """Read-only bridge presenting certification as cards."""

    def cards_for(self, result: CertificationResult) -> Tuple[ExecutionCard, ...]:
        verdict = "ok" if result.certified else "warn"
        return (
            ExecutionCard(
                card_id="cert-status",
                title="Mission Certified",
                summary=str(result.certified),
                detail="{0}/{1} criteria met".format(result.met_count, result.total),
                verdict=verdict,
            ),
            ExecutionCard(
                card_id="cert-no-network",
                title="No Network",
                summary="No network / HTTP / socket",
                detail="No connector/provider",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="cert-no-subprocess",
                title="No Subprocess",
                summary="No subprocess spawned",
                detail="Sync & deterministic",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="cert-plan-only",
                title="Lifecycle Only",
                summary="Manages definition/state/coordination",
                detail="Never executes",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="cert-sprint",
                title="Certification Sprint 143",
                summary="Certifier, score, manifest, validator, summary",
                detail="Mission Certified",
                verdict="ok",
            ),
        )

    def verdict_card(self, result: CertificationResult) -> ExecutionCard:
        return ExecutionCard(
            card_id="cert-card",
            title="Mission Runtime Certified",
            summary="lifecycle-only, deterministic, frozen DTOs",
            detail="Phase XIII complete",
            verdict="ok" if result.certified else "warn",
        )
