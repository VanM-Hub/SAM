"""
OP-287 — Hallucination Guard

Validasi claim terhadap evidence.
Bukan fact generation — hanya verifikasi.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


class ClaimStatus:
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ClaimVerdict:
    claim: str
    status: str  # supported | unsupported | unknown
    matched_evidence_id: str = ""
    matched_evidence_content: str = ""
    match_score: float = 0.0
    confidence_adjustment: float = 0.0  # negative for unsupported

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "status": self.status,
            "matched_evidence_id": self.matched_evidence_id,
            "match_score": self.match_score,
            "confidence_adjustment": self.confidence_adjustment,
        }


@dataclass(frozen=True)
class GuardResult:
    claims: tuple[ClaimVerdict, ...]
    total_claims: int = 0
    supported_count: int = 0
    unsupported_count: int = 0
    unknown_count: int = 0
    warnings: tuple[str, ...] = ()
    adjusted_confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_claims": self.total_claims,
            "supported_count": self.supported_count,
            "unsupported_count": self.unsupported_count,
            "unknown_count": self.unknown_count,
            "warnings": list(self.warnings),
            "adjusted_confidence": self.adjusted_confidence,
        }


class HallucinationGuard:
    """
    Validasi claim terhadap evidence.

    Setiap claim dalam LLM response diperiksa terhadap evidence yang tersedia.
    Tidak menghasilkan fact — hanya menandai mana yang didukung vs tidak.
    """

    def validate(self, response: str, evidence_set: Any,
                 original_confidence: float = 1.0) -> GuardResult:
        """
        Validate response claims against evidence set.
        """
        if not evidence_set:
            return GuardResult(
                claims=(),
                total_claims=0,
                warnings=("No evidence provided for validation.",),
                adjusted_confidence=0.5,
            )

        # Extract simple claims (sentences with substance)
        claims = self._extract_claims(response)
        if not claims:
            return GuardResult(
                claims=(),
                total_claims=0,
                adjusted_confidence=original_confidence,
            )

        evidence_items = getattr(evidence_set, 'items', []) or \
                         getattr(evidence_set, 'items', ())
        evidence_texts = [e.content.lower() for e in evidence_items]

        verdicts: list[ClaimVerdict] = []
        warnings: list[str] = []

        for claim in claims:
            verdict = self._check_claim(claim, evidence_items, evidence_texts)
            verdicts.append(verdict)
            if verdict.status == ClaimStatus.UNSUPPORTED:
                warnings.append(
                    f"Claim tidak didukung evidence: '{claim[:80]}...'"
                )

        total = len(verdicts)
        supported = sum(1 for v in verdicts if v.status == ClaimStatus.SUPPORTED)
        unsupported = sum(1 for v in verdicts if v.status == ClaimStatus.UNSUPPORTED)
        unknown = sum(1 for v in verdicts if v.status == ClaimStatus.UNKNOWN)

        adj_confidence = original_confidence
        if total > 0:
            adj_confidence = round(
                original_confidence * (supported / total), 2
            )

        return GuardResult(
            claims=tuple(verdicts),
            total_claims=total,
            supported_count=supported,
            unsupported_count=unsupported,
            unknown_count=unknown,
            warnings=tuple(warnings),
            adjusted_confidence=adj_confidence,
        )

    def _extract_claims(self, text: str) -> list[str]:
        """Extract claims from text (simple sentence split)."""
        sentences = text.replace("\n", " ").split(".")
        claims: list[str] = []
        for s in sentences:
            stripped = s.strip()
            # Filter: must have at least 10 chars and look like a claim
            if len(stripped) >= 10 and not stripped.startswith(
                ("what", "how", "why", "which", "who", "when", "is ", "are ", "can ")
            ):
                claims.append(stripped)
        return claims[:10]  # Limit to first 10 claims

    def _check_claim(self, claim: str,
                     evidence_items: list,
                     evidence_texts: list[str]) -> ClaimVerdict:
        """Check a single claim against evidence."""
        claim_lower = claim.lower()
        keywords = list(set(claim_lower.split()))[:5]

        best_score = 0.0
        best_evidence_id = ""
        best_evidence_content = ""

        for i, ev_text in enumerate(evidence_texts):
            match_count = sum(1 for kw in keywords if kw in ev_text)
            if len(keywords) > 0:
                score = match_count / len(keywords)
            else:
                score = 0.0

            if score > best_score:
                best_score = score
                if i < len(evidence_items):
                    best_evidence_id = evidence_items[i].id
                    best_evidence_content = ev_text[:100]

        if best_score >= 0.6:
            status = ClaimStatus.SUPPORTED
            adj = 0.0
        elif best_score >= 0.3:
            status = ClaimStatus.UNKNOWN
            adj = -0.1
        else:
            status = ClaimStatus.UNSUPPORTED
            adj = -0.3

        return ClaimVerdict(
            claim=claim[:100],
            status=status,
            matched_evidence_id=best_evidence_id,
            matched_evidence_content=best_evidence_content,
            match_score=round(best_score, 2),
            confidence_adjustment=adj,
        )
