"""Adaptive Governance - Learning Foundation - WP-01..10 (MISSION-5.6).

Experience learning model, dataset, classification, outcome correlation,
pattern detection, context, history, explainability, compliance.
Adaptive Governance HANYA belajar/mengevaluasi; tidak mengambil alih authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class OutcomeClass(str, Enum):
    """Klasifikasi outcome pengalaman."""

    SUCCESS = "success"
    FAILURE = "failure"
    UNCERTAIN = "uncertain"


class LearningSource(str, Enum):
    """Sumber pengalaman."""

    EXECUTION = "execution"
    SIMULATION = "simulation"
    OBSERVATION = "observation"


@dataclass(frozen=True)
class ExperienceSample:
    """Satu sampel pengalaman governance."""

    sample_id: str
    source: LearningSource
    outcome: OutcomeClass
    recorded_at: str = field(default_factory=_now_utc)
    attributes: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def attr(self, key: str) -> Optional[str]:
        for k, v in self.attributes:
            if k == key:
                return v
        return None

    def as_dict(self) -> dict:
        return {
            "sample_id": self.sample_id,
            "source": self.source.value,
            "outcome": self.outcome.value,
            "recorded_at": self.recorded_at,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class LearningContext:
    """Konteks pembelajaran."""

    scope: str
    governance_domain: str

    def as_dict(self) -> dict:
        return {"scope": self.scope, "governance_domain": self.governance_domain}


class LearningDataset:
    """Dataset pengalaman untuk pembelajaran."""

    def __init__(self) -> None:
        self._samples: list = []

    def add(self, sample: ExperienceSample) -> None:
        self._samples.append(sample)

    def samples(self) -> Tuple[ExperienceSample, ...]:
        return tuple(self._samples)

    def by_source(self, source: LearningSource) -> Tuple[ExperienceSample, ...]:
        return tuple(s for s in self._samples if s.source == source)

    def size(self) -> int:
        return len(self._samples)


class ExperienceClassifier:
    """Mengklasifikasi pengalaman."""

    def classify(self, sample: ExperienceSample) -> OutcomeClass:
        if sample.attr("error"):
            return OutcomeClass.FAILURE
        return sample.outcome


@dataclass(frozen=True)
class Correlation:
    """Korelasi attribute -> outcome."""

    attribute: str
    outcome: OutcomeClass
    strength: float

    def as_dict(self) -> dict:
        return {"attribute": self.attribute, "outcome": self.outcome.value, "strength": self.strength}


class OutcomeCorrelator:
    """Mengukur korelasi outcome."""

    def correlate(self, dataset: LearningDataset, attribute: str) -> Correlation:
        samples = dataset.samples()
        if not samples:
            return Correlation(attribute, OutcomeClass.UNCERTAIN, 0.0)
        matched = [s for s in samples if s.attr(attribute) is not None]
        successes = sum(1 for s in matched if s.outcome == OutcomeClass.SUCCESS)
        strength = (successes / len(matched)) if matched else 0.0
        outcome = OutcomeClass.SUCCESS if strength >= 0.5 else (OutcomeClass.FAILURE if matched and strength == 0 else OutcomeClass.UNCERTAIN)
        return Correlation(attribute, outcome, strength)


@dataclass(frozen=True)
class Pattern:
    """Pola yang terdeteksi."""

    pattern_id: str
    attribute: str
    value: str
    confidence: float

    def as_dict(self) -> dict:
        return {"pattern_id": self.pattern_id, "attribute": self.attribute, "value": self.value, "confidence": self.confidence}


class PatternDetector:
    """Mendeteksi pola dari dataset."""

    def detect(self, dataset: LearningDataset, attribute: str, value: str) -> Pattern:
        samples = dataset.samples()
        if not samples:
            return Pattern("p-0", attribute, value, 0.0)
        matching = [s for s in samples if s.attr(attribute) == value]
        ratio = len(matching) / len(samples)
        confidence = min(1.0, ratio * 2)
        return Pattern(f"p-{len(samples)}", attribute, value, round(confidence, 3))


@dataclass(frozen=True)
class LearningHistoryEntry:
    """Entri history pembelajaran."""

    pattern_id: str
    recorded_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {"pattern_id": self.pattern_id, "recorded_at": self.recorded_at}


class LearningHistory:
    """History pembelajaran (append-only)."""

    def __init__(self) -> None:
        self._entries: list = []

    def record(self, pattern: Pattern) -> None:
        self._entries.append(LearningHistoryEntry(pattern.pattern_id))

    def entries(self) -> Tuple[LearningHistoryEntry, ...]:
        return tuple(self._entries)


class LearningExplainability:
    """Menjelaskan pembelajaran."""

    def explain(self, pattern: Pattern) -> Dict[str, Any]:
        return {
            "pattern_id": pattern.pattern_id,
            "attribute": pattern.attribute,
            "value": pattern.value,
            "confidence": pattern.confidence,
            "learned": True,
        }


class LearningComplianceChecker:
    """Checker compliance pembelajaran (tidak mengambil authority)."""

    def check(self, *, learn_only=True, no_authority_change=True, no_auto_apply=True, evidence_based=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "LEARN_ONLY", "passed": learn_only},
            {"code": "NO_AUTHORITY_CHANGE", "passed": no_authority_change},
            {"code": "NO_AUTO_APPLY", "passed": no_auto_apply},
            {"code": "EVIDENCE_BASED", "passed": evidence_based},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "adaptive_governance.learning", "passed": passed, "certified": passed, "checks": [c for c in checks]}
