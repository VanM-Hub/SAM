# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 143 - Mission Certification: conversation_certification.

Read-only conversation bridge for certification.
"""
from __future__ import annotations

from typing import Dict, Tuple

from .mission_certification import MissionCertifier, CertificationResult


class ConversationCertificationBridge:
    """Read-only bridge exposing certification info."""

    def __init__(self, certifier: MissionCertifier) -> None:
        self._certifier = certifier

    def certify(self) -> CertificationResult:
        return self._certifier.certify()

    def criteria_met(self, result: CertificationResult) -> int:
        return result.met_count

    def summary(self, result: CertificationResult) -> Dict[str, int]:
        return {
            "met": result.met_count,
            "total": result.total,
            "certified": int(result.certified),
        }
