"""
OP-117 — Failure Pattern Analyzer.

Audit semua kegagalan. Kelompokkan berdasarkan tipe.
Hitung frekuensi, trend, severity. Rekomendasi perbaikan.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


FailureType = Literal[
    "wrong_recommendation",
    "missing_evidence",
    "bad_prediction",
    "execution_failure",
    "verification_failure",
    "rollback",
    "human_override",
    "timeout",
    "unknown",
]

FAILURE_LABELS = {
    "wrong_recommendation": "Wrong Recommendation",
    "missing_evidence": "Missing Evidence",
    "bad_prediction": "Bad Prediction",
    "execution_failure": "Execution Failure",
    "verification_failure": "Verification Failure",
    "rollback": "Rollback",
    "human_override": "Human Override",
    "timeout": "Timeout",
    "unknown": "Unknown",
}

FAILURE_SEVERITY = {
    "wrong_recommendation": "HIGH",
    "missing_evidence": "MEDIUM",
    "bad_prediction": "MEDIUM",
    "execution_failure": "HIGH",
    "verification_failure": "HIGH",
    "rollback": "MEDIUM",
    "human_override": "LOW",
    "timeout": "LOW",
    "unknown": "MEDIUM",
}

FAILURE_FIX_SUGGESTIONS = {
    "wrong_recommendation": "Review scoring weights and evidence quality",
    "missing_evidence": "Improve observation completeness",
    "bad_prediction": "Calibrate confidence thresholds",
    "execution_failure": "Check sandbox and executor configuration",
    "verification_failure": "Review verification checkers and thresholds",
    "rollback": "Audit rollback procedures",
    "human_override": "Review decision explanation quality",
    "timeout": "Check pipeline timeout settings",
    "unknown": "Investigate and classify failure",
}


@dataclass
class FailureRecord:
    """Satu record kegagalan."""
    failure_type: str
    decision_title: str
    severity: str
    timestamp: str
    detail: str = ""

    def to_dict(self) -> dict:
        return {
            "type": self.failure_type,
            "label": FAILURE_LABELS.get(self.failure_type, self.failure_type),
            "decision": self.decision_title,
            "severity": self.severity,
        }


@dataclass
class FailurePattern:
    """Pola untuk satu tipe kegagalan."""
    failure_type: str
    label: str
    frequency: int = 0
    trend: str = "stable"           # "increasing", "stable", "decreasing"
    severity: str = "MEDIUM"
    recommended_fix: str = ""
    records: List[FailureRecord] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.failure_type,
            "label": self.label,
            "frequency": self.frequency,
            "trend": self.trend,
            "severity": self.severity,
            "recommended_fix": self.recommended_fix,
            "count": len(self.records),
        }


@dataclass
class FailureAnalysis:
    """Analisis lengkap semua kegagalan."""
    patterns: List[FailurePattern] = field(default_factory=list)
    total_failures: int = 0
    most_common: str = ""
    highest_severity: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "total_failures": self.total_failures,
            "most_common": self.most_common,
            "highest_severity": self.highest_severity,
            "patterns": [p.to_dict() for p in self.patterns],
        }

    def to_text(self) -> str:
        lines = [
            "=== Failure Pattern Analysis ===",
            "Total failures: {}".format(self.total_failures),
            "Most common: {}".format(self.most_common),
            "Highest severity: {}".format(self.highest_severity),
            "",
        ]
        for p in sorted(self.patterns, key=lambda x: x.frequency, reverse=True):
            lines.append("  {label}: {freq}x ({trend}) — {fix}".format(
                label=p.label, freq=p.frequency, trend=p.trend, fix=p.recommended_fix))
        return "\n".join(lines)


class FailureAnalyzer:
    """Analyzer untuk pola kegagalan.

    Method:
      record(type, title, detail) — catat kegagalan
      analyze() -> FailureAnalysis — hasilkan analisis
    """

    def __init__(self):
        self._records: List[FailureRecord] = []
        self._by_type: Dict[str, List[str]] = {}  # type → [timestamps]

    def record(self, failure_type: str, decision_title: str,
               detail: str = "") -> FailureRecord:
        """Catat satu kegagalan."""
        severity = FAILURE_SEVERITY.get(failure_type, "MEDIUM")
        record = FailureRecord(
            failure_type=failure_type,
            decision_title=decision_title,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            detail=detail,
        )
        self._records.append(record)
        self._by_type.setdefault(failure_type, []).append(record.timestamp)
        return record

    def analyze(self) -> FailureAnalysis:
        """Analisis semua kegagalan yang tercatat."""
        if not self._records:
            return FailureAnalysis()

        patterns: List[FailurePattern] = []
        total = len(self._records)

        for ftype in set(r.failure_type for r in self._records):
            type_records = [r for r in self._records if r.failure_type == ftype]
            freq = len(type_records)

            # Trend: bandingkan first half vs second half
            timestamps = sorted(self._by_type.get(ftype, []))
            mid = len(timestamps) // 2
            first_half = timestamps[:mid] if mid > 0 else []
            second_half = timestamps[mid:] if mid > 0 else timestamps
            if len(first_half) >= 2 and len(second_half) >= 2:
                if len(second_half) > len(first_half) * 1.3:
                    trend = "increasing"
                elif len(second_half) < len(first_half) * 0.7:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "stable"

            patterns.append(FailurePattern(
                failure_type=ftype,
                label=FAILURE_LABELS.get(ftype, ftype),
                frequency=freq,
                trend=trend,
                severity=FAILURE_SEVERITY.get(ftype, "MEDIUM"),
                recommended_fix=FAILURE_FIX_SUGGESTIONS.get(ftype, "Investigate"),
                records=type_records,
            ))

        patterns.sort(key=lambda p: p.frequency, reverse=True)
        most_common = patterns[0].label if patterns else ""
        highest_sev = "CRITICAL" if any(p.severity == "HIGH" for p in patterns) else \
                      "HIGH" if any(p.severity == "HIGH" for p in patterns) else \
                      "MEDIUM"

        return FailureAnalysis(
            patterns=patterns,
            total_failures=total,
            most_common=most_common,
            highest_severity=highest_sev,
        )
