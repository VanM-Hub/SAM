"""
OP-346 — Conversation Governance Bridge

Query read-only untuk governance:
  - why_blocked, why_approved
  - execution_readiness, risk_summary
  - policy_summary, guardian_summary
  - pending_requirements, missing_approvals
  - operational_explanation, governance_report
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


QUERIES = [
    "why_blocked", "why_approved",
    "execution_readiness", "risk_summary",
    "policy_summary", "guardian_summary",
    "pending_requirements", "missing_approvals",
    "operational_explanation", "governance_report",
]


@dataclass(frozen=True)
class GovernanceConversationQuery:
    """DTO untuk query governance conversation."""
    query_type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GovernanceConversationResponse:
    """Response dari governance conversation."""
    success: bool
    query_type: str
    data: Optional[Dict[str, Any]] = None
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "query_type": self.query_type,
            "data": self.data,
            "error": self.error,
        }


class GovernanceConversationBridge:
    """Bridge conversation untuk governance queries. Read-only."""

    def __init__(
        self,
        governance: Any = None,
        readiness: Any = None,
        risk_assessment: Any = None,
        explanation: Any = None,
    ):
        self._governance = governance
        self._readiness = readiness
        self._risk_assessment = risk_assessment
        self._explanation = explanation
        self._query_count = 0

    @property
    def query_count(self) -> int:
        return self._query_count

    def query(self, query_type: str, **kwargs: Any) -> GovernanceConversationResponse:
        """Jalankan satu query governance.

        Args:
            query_type: Salah satu dari 10 query types.
            **kwargs: Parameter query.

        Returns:
            GovernanceConversationResponse immutable.
        """
        self._query_count += 1
        qtype = query_type.lower().replace(" ", "_")

        handler = getattr(self, f"_handle_{qtype}", None)
        if handler is None:
            return GovernanceConversationResponse(
                success=False, query_type=query_type,
                error=f"Query type '{query_type}' tidak dikenal. "
                      f"Pilihan: {', '.join(QUERIES)}",
            )

        try:
            result = handler(**kwargs)
            return GovernanceConversationResponse(
                success=True, query_type=query_type, data=result,
            )
        except Exception as e:
            return GovernanceConversationResponse(
                success=False, query_type=query_type, error=str(e),
            )

    def _extract_gov_status(self) -> Dict[str, Any]:
        """Ambil status governance dari engine."""
        if not self._governance:
            return {"governance_status": "unknown", "governance_score": 0.0}
        # Evaluate with defaults
        r = self._governance.evaluate()
        return {
            "governance_status": r.overall_status.value,
            "governance_score": r.overall_score,
            "approved": r.approved,
            "stage_count": r.stage_count,
            "failed_stages": r.failed_stages,
            "stages": [s.stage.value for s in r.stages],
        }

    def _handle_why_blocked(self, **kw: Any) -> Dict[str, Any]:
        """Mengapa operasi diblokir."""
        ready = None
        if self._readiness:
            ready = self._readiness.evaluate(**kw)
            if ready.ready:
                return {
                    "blocked": False,
                    "message": "Operasi tidak diblokir",
                    "readiness_level": ready.overall_level.value,
                }
            return {
                "blocked": True,
                "readiness_level": ready.overall_level.value,
                "blocking_dimensions": list(ready.blocking_dimensions),
                "summary": ready.summary,
                "recommendations": list(ready.recommendations),
            }
        return {"blocked": True, "message": "Readiness evaluator tidak tersedia"}

    def _handle_why_approved(self, **kw: Any) -> Dict[str, Any]:
        """Mengapa operasi disetujui."""
        gov = self._extract_gov_status()
        if not self._governance:
            return {"approved": True, "message": "Governance tidak tersedia"}

        r = self._governance.evaluate(**kw)
        if r.approved:
            stages_detail = []
            for s in r.stages:
                stages_detail.append({
                    "stage": s.stage.value, "status": s.status.value,
                    "score": s.score, "reason": s.reason,
                })
            return {
                "approved": True,
                "governance_score": r.overall_score,
                "stages": stages_detail,
                "summary": r.summary,
                "message": "Semua stage governance lolos",
            }
        return {
            "approved": False,
            "governance_score": r.overall_score,
            "summary": r.summary,
            "failed_stages": r.failed_stages,
        }

    def _handle_execution_readiness(self, **kw: Any) -> Dict[str, Any]:
        """Status readiness eksekusi."""
        if not self._readiness:
            return {"readiness": "unknown", "message": "Readiness evaluator tidak tersedia"}
        r = self._readiness.evaluate(**kw)
        return {
            "readiness_level": r.overall_level.value,
            "ready": r.ready,
            "score": r.overall_score,
            "checks": [{"dimension": c.dimension, "passed": c.passed,
                        "level": c.level.value, "detail": c.detail}
                       for c in r.checks],
            "blocking": list(r.blocking_dimensions),
            "recommendations": list(r.recommendations),
            "summary": r.summary,
        }

    def _handle_risk_summary(self, **kw: Any) -> Dict[str, Any]:
        """Ringkasan risk assessment."""
        if not self._risk_assessment:
            return {"risk": "unknown", "message": "Risk assessment tidak tersedia"}
        r = self._risk_assessment.assess(**kw)
        return {
            "overall_level": r.overall_level.value,
            "overall_score": r.overall_score,
            "is_safe": r.is_safe,
            "dimensions": [{"dimension": d.dimension, "level": d.level.value,
                           "score": d.score, "significant": d.is_significant}
                          for d in r.dimensions],
            "top_risks": list(r.top_risks),
            "mitigations": list(r.mitigations),
            "summary": r.summary,
        }

    def _handle_policy_summary(self, **kw: Any) -> Dict[str, Any]:
        """Ringkasan policy compliance."""
        gov = self._extract_gov_status()
        ready = None
        if self._readiness:
            ready = self._readiness.evaluate(**kw)
            policy_checks = [c for c in ready.checks if c.dimension == "policy"]
        else:
            policy_checks = []

        return {
            "governance_policy_status": gov.get("governance_status", "unknown"),
            "readiness_policy": [
                {"dimension": c.dimension, "passed": c.passed,
                 "level": c.level.value, "detail": c.detail}
                for c in policy_checks
            ] if policy_checks else [],
            "message": "Policy summary dari governance + readiness",
        }

    def _handle_guardian_summary(self, **kw: Any) -> Dict[str, Any]:
        """Ringkasan guardian health dan status."""
        gov = self._extract_gov_status()
        return {
            "governance": {
                "status": gov.get("governance_status", "unknown"),
                "score": gov.get("governance_score", 0.0),
                "stages": gov.get("stages", []),
            },
            "guardian_engine": {
                "available": all([
                    self._governance is not None,
                    self._readiness is not None,
                    self._risk_assessment is not None,
                ]),
            },
            "message": "Guardian summary dari governance pipeline",
        }

    def _handle_pending_requirements(self, **kw: Any) -> Dict[str, Any]:
        """Persyaratan yang masih pending."""
        pending: List[str] = []
        if self._readiness:
            r = self._readiness.evaluate(**kw)
            for c in r.checks:
                if not c.passed:
                    pending.append(f"{c.dimension}: {c.recommendation}")
        return {
            "pending_count": len(pending),
            "pending": pending,
            "summary": f"{len(pending)} requirement(s) pending",
        }

    def _handle_missing_approvals(self, **kw: Any) -> Dict[str, Any]:
        """Approval yang masih kurang."""
        missing = kw.get("approval_missing", 0)
        required = kw.get("approval_required", 0)
        granted = kw.get("approval_granted", required)
        return {
            "approval_required": required,
            "approval_granted": granted,
            "approval_missing": missing,
            "complete": missing == 0 and granted >= required,
            "summary": f"{granted}/{required} approvals granted"
                       if required > 0 else "No approvals required",
        }

    def _handle_operational_explanation(self, **kw: Any) -> Dict[str, Any]:
        """Penjelasan operasional lengkap."""
        if not self._explanation:
            return {"explanation": {}, "message": "Explanation engine tidak tersedia"}
        # Ambil status dari engine lain untuk konteks
        gov = self._extract_gov_status()
        expl_kw = dict(kw)
        expl_kw["governance_status"] = gov.get("governance_status", "unknown")
        expl_kw["governance_score"] = gov.get("governance_score", 0.0)
        r = self._explanation.build(**expl_kw)
        return {
            "decision": r.decision,
            "summary": r.summary,
            "sections": [{"title": s.title, "content": list(s.content), "level": s.level}
                        for s in r.sections],
            "next_actions": list(r.next_actions),
        }

    def _handle_governance_report(self, **kw: Any) -> Dict[str, Any]:
        """Laporan governance lengkap."""
        report = {
            "governance": self._extract_gov_status(),
            "readiness": {},
            "risk": {},
            "explanation": {},
        }

        if self._readiness:
            r = self._readiness.evaluate(**kw)
            report["readiness"] = {
                "level": r.overall_level.value,
                "score": r.overall_score,
                "blocking": list(r.blocking_dimensions),
                "summary": r.summary,
            }

        if self._risk_assessment:
            risk = self._risk_assessment.assess(**kw)
            report["risk"] = {
                "level": risk.overall_level.value,
                "score": risk.overall_score,
                "top_risks": list(risk.top_risks),
                "summary": risk.summary,
            }

        if self._explanation:
            expl_kw = dict(kw)
            expl_kw.update(report["governance"])
            exp = self._explanation.build(**expl_kw)
            report["explanation"] = {
                "decision": exp.decision,
                "summary": exp.summary,
                "sections": [s.title for s in exp.sections],
                "next_actions": list(exp.next_actions),
            }

        return report
