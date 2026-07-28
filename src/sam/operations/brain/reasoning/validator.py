"""
OP-295 — Response Validator V2

Validasi response LLM sebelum disajikan ke pengguna.
Mendeteksi: empty answer, hallucination score, unsupported claim,
duplicated evidence, invalid citation, confidence mismatch, malformed response.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class ValidationIssue:
    code: str  # EMPTY_ANSWER, HALLUCINATION, UNSUPPORTED_CLAIM, DUPLICATE_EVIDENCE,
    #            INVALID_CITATION, CONFIDENCE_MISMATCH, MALFORMED_RESPONSE
    severity: str  # error, warning, info
    message: str
    field: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "field": self.field,
        }


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    issues: Tuple[ValidationIssue, ...] = ()
    total_issues: int = 0
    errors: int = 0
    warnings: int = 0
    info: int = 0
    overall_score: float = 1.0  # 0.0 - 1.0
    validated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "total_issues": self.total_issues,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "overall_score": self.overall_score,
            "issues": [i.to_dict() for i in self.issues],
            "validated_at": self.validated_at,
        }


class ResponseValidator:
    """
    Validasi LLM response.

    Pemeriksaan:
    1. Empty answer
    2. Hallucination score vs confidence mismatch
    3. Unsupported claims
    4. Duplicated evidence
    5. Invalid citation format
    6. Malformed response (JSON / markdown)
    7. Confidence out of range
    """

    def validate(self, answer: str,
                 confidence: float = 1.0,
                 evidence_ids: Optional[Tuple[str, ...]] = None,
                 citations: Optional[Tuple[Any, ...]] = None,
                 unsupported_claims: Optional[Tuple[str, ...]] = None,
                 supported_claims: int = 0,
                 total_claims: int = 0,
                 required_evidence: bool = False,
                 ) -> ValidationReport:
        """Validasi penuh response."""
        issues: list[ValidationIssue] = []

        # 1. Empty answer
        if not answer or not answer.strip():
            issues.append(ValidationIssue(
                code="EMPTY_ANSWER",
                severity="error",
                message="Response is empty",
                field="answer",
            ))

        # 2. Confidence mismatch / hallucination
        if not answer or not answer.strip():
            pass  # Already caught
        elif total_claims > 0 and supported_claims == 0 and confidence > 0.5:
            issues.append(ValidationIssue(
                code="CONFIDENCE_MISMATCH",
                severity="warning",
                message=(
                    f"Confidence {confidence} but {supported_claims}/{total_claims} "
                    f"claims supported",
                ),
                field="confidence",
            ))

        # 3. Unsupported claims
        if unsupported_claims and len(unsupported_claims) > 0:
            for claim in unsupported_claims[:5]:
                issues.append(ValidationIssue(
                    code="UNSUPPORTED_CLAIM",
                    severity="warning",
                    message=f"Claim tidak didukung evidence: {claim[:80]}",
                    field="answer",
                ))

        # 4. Duplicated evidence
        if evidence_ids:
            dupes = self._find_duplicates(evidence_ids)
            for d in dupes:
                issues.append(ValidationIssue(
                    code="DUPLICATE_EVIDENCE",
                    severity="info",
                    message=f"Evidence ID duplikat: {d}",
                    field="evidence_ids",
                ))

        # 5. Invalid citation
        if citations:
            for i, c in enumerate(citations):
                if isinstance(c, tuple) and len(c) == 2:
                    if not isinstance(c[0], str) or not isinstance(c[1], (int, float)):
                        issues.append(ValidationIssue(
                            code="INVALID_CITATION",
                            severity="warning",
                            message=f"Citation ke-{i} format tidak valid",
                            field="citations",
                        ))

        # 6. Malformed response (JSON check)
        if answer:
            malformed = self._check_malformed(answer)
            if malformed:
                issues.append(ValidationIssue(
                    code="MALFORMED_RESPONSE",
                    severity="warning",
                    message=malformed,
                    field="answer",
                ))

        # 7. Confidence out of range
        if not (0.0 <= confidence <= 1.0):
            issues.append(ValidationIssue(
                code="CONFIDENCE_MISMATCH",
                severity="error",
                message=f"Confidence {confidence} di luar range [0,1]",
                field="confidence",
            ))

        # 8. Required evidence not provided
        if required_evidence and (not evidence_ids or len(evidence_ids) == 0):
            issues.append(ValidationIssue(
                code="UNSUPPORTED_CLAIM",
                severity="warning",
                message="Required evidence not provided",
                field="evidence_ids",
            ))

        errors = sum(1 for i in issues if i.severity == "error")
        warnings = sum(1 for i in issues if i.severity == "warning")
        infos = sum(1 for i in issues if i.severity == "info")

        score = self._compute_score(issues, errors, warnings)

        return ValidationReport(
            passed=errors == 0,
            issues=tuple(issues),
            total_issues=len(issues),
            errors=errors,
            warnings=warnings,
            info=infos,
            overall_score=score,
            validated_at=datetime.now().isoformat(timespec="seconds"),
        )

    def _find_duplicates(self, ids: Tuple[str, ...]) -> Tuple[str, ...]:
        seen: set[str] = set()
        dupes: list[str] = []
        for i in ids:
            if i in seen:
                dupes.append(i)
            seen.add(i)
        return tuple(dupes)

    def _check_malformed(self, answer: str) -> str:
        """Detect malformed patterns."""
        # JSON yang tidak lengkap
        if answer.startswith("{") and not answer.endswith("}"):
            return "JSON tidak lengkap (kurang tutup kurung)"
        if answer.startswith("[") and not answer.endswith("]"):
            return "JSON array tidak lengkap"
        # Markdown yang tidak balanced
        if answer.count("```") % 2 != 0:
            return "Markdown code block tidak balanced"
        return ""

    def _compute_score(self, issues: list,
                        errors: int, warnings: int) -> float:
        if not issues:
            return 1.0
        total_penalty = errors * 0.3 + warnings * 0.1
        score = max(0.0, 1.0 - total_penalty)
        return round(score, 2)
