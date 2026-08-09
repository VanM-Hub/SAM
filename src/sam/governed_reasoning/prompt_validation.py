"""Prompt Validation - WP-04 (MISSION-4.4 / IP-4.4-001).

Memastikan Prompt tervalidasi sebelum dikirim ke Provider. Prompt yang gagal
tidak dikirim, alasan validasi tersedia, validation menghasilkan audit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from .prompt_model import Prompt


@dataclass(frozen=True)
class ValidationResult:
    """Hasil validasi prompt."""

    prompt_id: str
    valid: bool
    reasons: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "valid": self.valid,
            "reasons": list(self.reasons),
        }


class PolicyVerification:
    """Verifikasi kebijakan prompt (max_tokens, evidence requirement)."""

    @staticmethod
    def verify(prompt: Prompt) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        valid = True
        tokens = len(prompt.content.split())
        if tokens > prompt.policy.max_tokens:
            valid = False
            reasons.append("exceeds max_tokens")
        if prompt.policy.require_evidence and not prompt.evidence_refs:
            valid = False
            reasons.append("missing evidence refs")
        return valid, reasons


class ContextVerification:
    """Verifikasi konteks prompt (ada classifier & purpose)."""

    @staticmethod
    def verify(prompt: Prompt) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        valid = True
        if not prompt.content.strip():
            valid = False
            reasons.append("empty content")
        if not prompt.metadata.classification:
            valid = False
            reasons.append("missing classification")
        return valid, reasons


class SafetyVerification:
    """Verifikasi keamanan prompt (deteksi pola berbahaya)."""

    DANGEROUS = (
        "ignore previous instructions",
        "system prompt",
        "reveal your",
        "bypass approval",
        "execute without approval",
    )

    @staticmethod
    def verify(prompt: Prompt) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        valid = True
        haystack = (prompt.content + " " + prompt.system).lower()
        for pattern in SafetyVerification.DANGEROUS:
            if pattern in haystack:
                valid = False
                reasons.append(f"unsafe pattern: {pattern}")
        return valid, reasons


class PromptValidator:
    """Validator prompt terpadu (policy + context + safety)."""

    def __init__(self) -> None:
        self._audit: List[Dict[str, str]] = []

    def validate(self, prompt: Prompt) -> ValidationResult:
        reasons: List[str] = []
        valid = True
        for verifier in (
            PolicyVerification.verify,
            ContextVerification.verify,
            SafetyVerification.verify,
        ):
            ok, rs = verifier(prompt)
            if not ok:
                valid = False
            reasons.extend(rs)
        self._audit.append(
            {
                "prompt_id": prompt.prompt_id,
                "valid": str(valid),
            }
        )
        return ValidationResult(
            prompt_id=prompt.prompt_id, valid=valid, reasons=tuple(reasons)
        )

    def audit_report(self) -> Tuple[Dict[str, str], ...]:
        return tuple(self._audit)


class ValidationExplainability:
    """Menjelaskan hasil validasi."""

    @staticmethod
    def explain(result: ValidationResult) -> Dict[str, Any]:
        return {
            "prompt_id": result.prompt_id,
            "message": (
                "Prompt is valid."
                if result.valid
                else "Prompt rejected: " + "; ".join(result.reasons)
            ),
            "rejected": not result.valid,
            "reasons": list(result.reasons),
        }
