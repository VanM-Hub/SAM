"""
DecisionAlternatives — Tiga level: Recommended, Alternative, Emergency.

Setiap keputusan minimal menghasilkan:
  Recommended — solusi utama
  Alternative — solusi kedua
  Emergency — jika alternatif gagal

Semua berdasarkan evidence yang sama.
Tidak ada tebakan.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .decision import DecisionProposal


@dataclass
class DecisionAlternatives:
    """Tiga level alternatif untuk satu situasi."""
    recommended: DecisionProposal
    alternative: Optional[DecisionProposal] = None
    emergency: Optional[DecisionProposal] = None

    def to_text(self) -> str:
        parts = ["### Recommended"]
        parts.append(self.recommended.to_text())
        if self.alternative:
            parts.append("\n### Alternative")
            parts.append(self.alternative.to_text())
        if self.emergency:
            parts.append("\n### Emergency")
            parts.append(self.emergency.to_text())
        return "\n".join(parts)

    def to_dict(self) -> dict:
        d = {"recommended": self.recommended.to_dict(), "anomaly_type": ""}
        if self.alternative:
            d["alternative"] = self.alternative.to_dict()
        if self.emergency:
            d["emergency"] = self.emergency.to_dict()
        return d


@dataclass
class AlternativesPackage:
    """Semua alternatif dari satu observasi."""
    alternatives: List[DecisionAlternatives] = field(default_factory=list)

    def has_any(self) -> bool:
        return len(self.alternatives) > 0


class AlternativesEngine:
    """Menghasilkan alternatif keputusan — Recommended, Alternative, Emergency.

    Untuk setiap anomali/observasi:
    1. Recommended — tindakan ideal berdasarkan evidence
    2. Alternative — jika recommended tidak bisa dijalankan kini
    3. Emergency — jika situasi memburuk
    """

    def __init__(self, runtime_provider=None, workspace_provider=None):
        self._rp = runtime_provider
        self._wp = workspace_provider

    def generate(self, anomaly_type: str = "",
                 anomaly_detail: str = "",
                 severity: str = "information",
                 value: Optional[float] = None,
                 threshold: Optional[float] = None,
                 evidence: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None) -> DecisionAlternatives:
        """Generate alternatif untuk satu anomali.

        Args:
            anomaly_type: Tipe anomali
            anomaly_detail: Detail tambahan
            severity: Tingkat keparahan
            value: Nilai terukur
            threshold: Ambang batas
            evidence: Evidence yang mendukung
            context: Data tambahan

        Returns:
            DecisionAlternatives dengan recommended + alternative + emergency.
        """
        ctx = context or {}
        ev = evidence or []
        evidence_count = len(ev)

        # Compute safe confidence
        def _conf(base: float, ev_count: int = 0) -> float:
            return max(0.0, min(1.0, base + ev_count * 0.05))

        if anomaly_type == "database_unavailable":
            return DecisionAlternatives(
                recommended=DecisionProposal(
                    decision="Restart database connection",
                    reason="Database is unavailable — restart is the fastest recovery",
                    confidence=_conf(0.8, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                ),
                alternative=DecisionProposal(
                    decision="Wait and retry connection (max 30s)",
                    reason="Database may be in temporary unresponsive state",
                    confidence=_conf(0.5, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    uncertainty="Waiting may not resolve if database process has crashed",
                    missing_information=["Database process status", "Last restart time"],
                ),
                emergency=DecisionProposal(
                    decision="Escalate to system administrator",
                    reason="Database unavailability persists after restart attempt",
                    confidence=_conf(0.9, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    blocking_conditions=[],
                ),
            )
        elif anomaly_type == "disk_exhaustion":
            return DecisionAlternatives(
                recommended=DecisionProposal(
                    decision="Free up disk space (remove temp + old logs)",
                    reason="Disk at {:.1f}% — cleanup avoids write failures".format(value or 0),
                    confidence=_conf(0.8, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                ),
                alternative=DecisionProposal(
                    decision="Compress and archive old data",
                    reason="Compression buys time without deleting data",
                    confidence=_conf(0.6, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    uncertainty="Compression requires CPU resources",
                    missing_information=["File types and compression ratios"],
                ),
                emergency=DecisionProposal(
                    decision="Execute emergency cleanup (remove all non-essential files)",
                    reason="Disk exhaustion imminent — must reclaim space immediately",
                    confidence=_conf(0.9, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    blocking_conditions=["Confirm no critical data will be deleted"],
                ),
            )
        elif anomaly_type == "cpu_spike":
            return DecisionAlternatives(
                recommended=DecisionProposal(
                    decision="Investigate CPU spike",
                    reason="CPU at {:.1f}% — identify the root cause first".format(value or 0),
                    confidence=_conf(0.7, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                ),
                alternative=DecisionProposal(
                    decision="Reduce process priority",
                    reason="Lower priority for non-critical processes consuming CPU",
                    confidence=_conf(0.5, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    uncertainty="Need per-process breakdown to identify which process to throttle",
                ),
                emergency=DecisionProposal(
                    decision="Restart worker process",
                    reason="CPU at critical level — restart clears memory leaks and runaway processes",
                    confidence=_conf(0.6, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    blocking_conditions=["Confirm restart will not corrupt active operations"],
                ),
            )
        elif anomaly_type == "queue_growth":
            return DecisionAlternatives(
                recommended=DecisionProposal(
                    decision="Drain pending queue",
                    reason="Queue depth: {} — operations are accumulating".format(value or 0),
                    confidence=_conf(0.75, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                ),
                alternative=DecisionProposal(
                    decision="Wait 5 minutes — monitor if queue self-recovers",
                    reason="Queue growth may be transient from burst activity",
                    confidence=_conf(0.4, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    uncertainty="Risk of queue overflow if growth continues",
                    missing_information=["Throughput trend (last 10 minutes)"],
                ),
                emergency=DecisionProposal(
                    decision="Increase processing capacity",
                    reason="Queue keeps growing — need more processing power",
                    confidence=_conf(0.7, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    blocking_conditions=["Confirm capacity increase is available"],
                ),
            )
        elif anomaly_type == "memory_high":
            return DecisionAlternatives(
                recommended=DecisionProposal(
                    decision="Investigate memory usage",
                    reason="Memory at {:.1f}% — identify the cause".format(value or 0),
                    confidence=_conf(0.7, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                ),
                alternative=DecisionProposal(
                    decision="Clear caches to reduce memory pressure",
                    reason="Cached data can be freed without affecting operations",
                    confidence=_conf(0.55, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    uncertainty="Clearing caches may temporarily degrade performance",
                ),
                emergency=DecisionProposal(
                    decision="Restart memory-intensive process",
                    reason="Memory near limit — risk of OOM termination",
                    confidence=_conf(0.6, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    blocking_conditions=["Save state before restarting"],
                ),
            )
        elif anomaly_type == "temp_accumulation":
            return DecisionAlternatives(
                recommended=DecisionProposal(
                    decision="Remove temp files older than 24 hours",
                    reason="{} temp files accumulated — safe to remove old ones".format(int(value or 0)),
                    confidence=_conf(0.8, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                ),
                alternative=DecisionProposal(
                    decision="Compress temp files instead of deleting",
                    reason="Compression preserves data while saving space",
                    confidence=_conf(0.5, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    uncertainty="Compression effectiveness depends on file types",
                ),
                emergency=DecisionProposal(
                    decision="Remove all temp files",
                    reason="Temp files consuming significant space — immediate cleanup needed",
                    confidence=_conf(0.85, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    blocking_conditions=["Verify no active processes using temp files"],
                ),
            )
        elif anomaly_type == "cache_explosion":
            return DecisionAlternatives(
                recommended=DecisionProposal(
                    decision="Clear outdated cache entries",
                    reason="Cache at {:.1f} MB — only clear stale entries".format(value or 0),
                    confidence=_conf(0.8, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                ),
                alternative=DecisionProposal(
                    decision="Reduce cache TTL configuration",
                    reason="Reduce future cache growth by shortening TTL",
                    confidence=_conf(0.6, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    uncertainty="Shorter TTL may increase load on backend services",
                ),
                emergency=DecisionProposal(
                    decision="Flush entire cache",
                    reason="Cache size critical — immediate reset needed",
                    confidence=_conf(0.7, evidence_count),
                    required_evidence=ev,
                    evidence_count=evidence_count,
                    blocking_conditions=["Expect temporary performance degradation after flush"],
                ),
            )

        # Unknown anomaly type — single generic proposal only
        return DecisionAlternatives(
            recommended=DecisionProposal(
                decision="Review unknown anomaly: {}".format(anomaly_type if anomaly_type else "Unknown"),
                reason="Anomaly type not recognized — manual review recommended",
                confidence=_conf(0.3, evidence_count),
                required_evidence=ev,
                evidence_count=evidence_count,
            ),
        )

    def generate_all(self, anomaly_detector=None,
                      runtime_provider=None,
                      workspace_provider=None) -> AlternativesPackage:
        """Generate alternatif untuk semua anomali."""
        rp = runtime_provider or self._rp
        all_alts = []

        if anomaly_detector:
            anomalies = anomaly_detector.detect_all()
            for a in anomalies:
                alt = self.generate(
                    anomaly_type=a.type,
                    anomaly_detail=a.detail or "",
                    severity=a.severity,
                    value=a.value,
                    threshold=a.threshold,
                    evidence=a.evidence,
                )
                all_alts.append(alt)

        return AlternativesPackage(alternatives=all_alts)
