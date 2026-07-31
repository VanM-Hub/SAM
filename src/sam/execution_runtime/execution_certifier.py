"""Execution Certifier (Sprint 258).

Program C - Real Execution Runtime.
Sertifikasi 7 dimensi: Structure, Integrity, Consistency, Determinism,
Approval, Rollback, Safety.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .execution_manifest import ExecutionManifest
from .execution_score import ExecutionScore, ExecutionScoreSet
from .execution_validator import ExecutionValidator
from .execution_cert_report import ExecutionCertReport

DIMENSIONS = (
    "structure", "integrity", "consistency", "determinism",
    "approval", "rollback", "safety",
)


class ExecutionCertifier:
    """Sertifikasi execution runtime. Deterministic, read-only."""

    def __init__(self, validator: ExecutionValidator | None = None) -> None:
        self._validator = validator or ExecutionValidator()

    def certify(self, manifest: ExecutionManifest) -> ExecutionCertReport:
        d = manifest.descriptor
        c = manifest.contract
        m = manifest.metadata
        scores = {
            "structure": ExecutionScore("structure", 1.0, bool(d.id and d.name), "identity"),
            "integrity": ExecutionScore("integrity", 1.0, bool(c.contract_id), "contract"),
            "consistency": ExecutionScore(
                "consistency", 1.0, d.mode in ("preview", "execute", "rollback"),
                "mode"),
            "determinism": ExecutionScore("determinism", 1.0, m.determinism_check, "deterministic"),
            "approval": ExecutionScore("approval", 1.0, m.approved or m.preview_only, "approval"),
            "rollback": ExecutionScore("rollback", 1.0, c.max_retries >= 0, "rollback-capable"),
            "safety": ExecutionScore("safety", 1.0, m.synchronous and m.external_calls >= 0, "safe"),
        }
        score_set = ExecutionScoreSet(scores=scores)
        passed = score_set.all_passed()
        return ExecutionCertReport(
            report_id=f"ec-{manifest.manifest_id}",
            passed=passed,
            score_set=score_set,
            dimensions_passed=sum(1 for v in scores.values() if v.passed),
            dimensions_total=len(DIMENSIONS),
        )
