"""
OP-345 — Guardian Coordination Runtime

Menggabungkan:
  Guardian Runtime V2
  ↓
  Governance
  ↓
  Readiness
  ↓
  Risk
  ↓
  Explanation

Tidak menjalankan mission. Synchronous. Immutable DTOs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CoordinationResult:
    """Hasil lengkap coordination pipeline."""
    coordination_id: str
    success: bool
    runtime_ok: bool = False
    governance_ok: bool = False
    readiness_ok: bool = False
    risk_ok: bool = False
    explanation_ok: bool = False
    runtime_result: Optional[Dict[str, Any]] = None
    governance_result: Optional[Dict[str, Any]] = None
    readiness_result: Optional[Dict[str, Any]] = None
    risk_result: Optional[Dict[str, Any]] = None
    explanation_result: Optional[Dict[str, Any]] = None
    errors: Tuple[str, ...] = field(default_factory=tuple)
    started_at: str = ""
    completed_at: str = ""

    @property
    def all_passed(self) -> bool:
        return all([self.runtime_ok, self.governance_ok,
                    self.readiness_ok, self.risk_ok, self.explanation_ok])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coordination_id": self.coordination_id,
            "success": self.success,
            "all_passed": self.all_passed,
            "runtime_ok": self.runtime_ok,
            "governance_ok": self.governance_ok,
            "readiness_ok": self.readiness_ok,
            "risk_ok": self.risk_ok,
            "explanation_ok": self.explanation_ok,
            "errors": list(self.errors),
        }


class GuardianCoordinationRuntime:
    """Coordination pipeline: Runtime V2 → Governance → Readiness → Risk → Explanation.

    Mengintegrasikan 5 subsystem. Hanya evaluasi. Tidak ada eksekusi.
    """

    def __init__(
        self,
        runtime_v2: Any = None,
        governance: Any = None,
        readiness: Any = None,
        risk_assessment: Any = None,
        explanation: Any = None,
    ):
        self._runtime_v2 = runtime_v2
        self._governance = governance
        self._readiness = readiness
        self._risk_assessment = risk_assessment
        self._explanation = explanation
        self._coordination_count = 0

    @property
    def coordination_count(self) -> int:
        return self._coordination_count

    def run(self, **kwargs: Any) -> CoordinationResult:
        """Jalankan coordination pipeline 5-stage."""
        import uuid
        from datetime import datetime
        cid = f"coord-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now().isoformat(timespec="seconds")
        self._coordination_count += 1
        errors: List[str] = []

        # Stage 1: Runtime V2
        runtime_ok = False
        runtime_data = None
        if self._runtime_v2:
            try:
                result_r2 = self._runtime_v2.run(**kwargs)
                runtime_ok = result_r2.success
                runtime_data = result_r2.to_dict() if hasattr(result_r2, "to_dict") else {
                    "success": result_r2.success, "stage_count": len(result_r2.stages)}
            except Exception as e:
                errors.append(f"runtime_v2: {e}")

        # Stage 2: Governance
        gov_result = None
        if self._governance:
            try:
                gov = self._governance.evaluate(**kwargs)
                gov_result = gov.to_dict() if hasattr(gov, "to_dict") else {
                    "overall_status": gov.overall_status.value}
            except Exception as e:
                errors.append(f"governance: {e}")
        governance_ok = gov_result is not None

        # Stage 3: Readiness
        ready_result = None
        if self._readiness:
            try:
                ready = self._readiness.evaluate(**kwargs)
                ready_result = ready.to_dict() if hasattr(ready, "to_dict") else {
                    "overall_level": ready.overall_level.value}
            except Exception as e:
                errors.append(f"readiness: {e}")
        readiness_ok = ready_result is not None

        # Stage 4: Risk
        risk_result = None
        if self._risk_assessment:
            try:
                risk = self._risk_assessment.assess(**kwargs)
                risk_result = risk.to_dict() if hasattr(risk, "to_dict") else {
                    "overall_level": risk.overall_level.value}
            except Exception as e:
                errors.append(f"risk: {e}")
        risk_ok = risk_result is not None

        # Stage 5: Explanation
        expl_result = None
        if self._explanation:
            try:
                # Build explanation params from previous results
                expl_kw = dict(kwargs)
                if gov_result:
                    expl_kw["governance_status"] = gov_result.get("overall_status", "unknown")
                    expl_kw["governance_score"] = gov_result.get("overall_score", 0.0)
                if ready_result:
                    expl_kw["readiness_level"] = ready_result.get("overall_level", "unknown")
                    expl_kw["readiness_score"] = ready_result.get("overall_score", 0.0)
                    expl_kw["readiness_blocking"] = tuple(ready_result.get("blocking_dimensions", []))
                if risk_result:
                    expl_kw["risk_level"] = risk_result.get("overall_level", "none")
                    expl_kw["risk_score"] = risk_result.get("overall_score", 0.0)
                    expl_kw["risk_dimensions"] = tuple(risk_result.get("top_risks", []))

                expl = self._explanation.build(**expl_kw)
                expl_result = expl.to_dict() if hasattr(expl, "to_dict") else {
                    "decision": expl.decision}
            except Exception as e:
                errors.append(f"explanation: {e}")
        explanation_ok = expl_result is not None

        completed_at = datetime.now().isoformat(timespec="seconds")
        success = len(errors) == 0

        return CoordinationResult(
            coordination_id=cid,
            success=success,
            runtime_ok=runtime_ok,
            governance_ok=governance_ok,
            readiness_ok=readiness_ok,
            risk_ok=risk_ok,
            explanation_ok=explanation_ok,
            runtime_result=runtime_data,
            governance_result=gov_result,
            readiness_result=ready_result,
            risk_result=risk_result,
            explanation_result=expl_result,
            errors=tuple(errors),
            started_at=started_at,
            completed_at=completed_at,
        )
