"""
DecisionPolicy — Proposal keputusan berbasis evidence.

Bukan action.
Bukan execution.
Hanya proposal.

Pipeline: Observation → Understanding → Decision → Conversation
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class DecisionProposal:
    """Satu proposal keputusan dengan evidence lengkap.

    Tidak ada confidence palsu.
    Tidak ada keputusan tanpa evidence.
    """
    decision: str                          # "Restart Worker", "Clean Cache", dll.
    reason: str                            # Kenapa keputusan ini diajukan
    confidence: float                       # 0.0 - 1.0
    required_evidence: List[str] = field(default_factory=list)
    blocking_conditions: List[str] = field(default_factory=list)
    source: str = "decision_policy"

    # Evidence tracking
    evidence_count: int = 0
    uncertainty: str = ""
    missing_information: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        parts = ["[{}] {} — {:.0f}% confidence.".format(
            "DECISION", self.decision, self.confidence * 100
        )]
        parts.append("  Reason: {}".format(self.reason))
        evidence_str = ", ".join(self.required_evidence[:3])
        if evidence_str:
            parts.append("  Evidence: {}".format(evidence_str))
        if self.uncertainty:
            parts.append("  Uncertainty: {}".format(self.uncertainty))
        if self.blocking_conditions:
            parts.append("  Blocked by: {}".format("; ".join(self.blocking_conditions)))
        return "\n".join(parts)

    def is_blocked(self) -> bool:
        return len(self.blocking_conditions) > 0

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "uncertainty": self.uncertainty,
            "missing_information": self.missing_information,
            "required_evidence": self.required_evidence,
            "blocking_conditions": self.blocking_conditions,
        }


@dataclass
class DecisionPackage:
    """Semua keputusan yang dihasilkan dari satu observasi."""
    proposals: List[DecisionProposal] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def has_any(self) -> bool:
        return len(self.proposals) > 0

    def get_not_blocked(self) -> List[DecisionProposal]:
        return [p for p in self.proposals if not p.is_blocked()]

    def get_blocked(self) -> List[DecisionProposal]:
        return [p for p in self.proposals if p.is_blocked()]

    def get_highest_confidence(self) -> Optional[DecisionProposal]:
        if not self.proposals:
            return None
        return max(self.proposals, key=lambda p: p.confidence)

    def to_text(self) -> str:
        if not self.proposals:
            return "No decisions required."
        parts = []
        for p in self.proposals:
            parts.append(p.to_text())
        return "\n\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "proposals": [p.to_dict() for p in self.proposals],
            "timestamp": self.timestamp,
            "count": len(self.proposals),
        }


class DecisionPolicy:
    """Policy untuk menghasilkan proposal keputusan dari evidence.

    Setiap proposal:
    - Harus punya reason
    - Harus punya confidence
    - Harus punya required_evidence
    - Boleh punya blocking_conditions (jika ada risiko)

    Jika evidence tidak cukup: confidence rendah, uncertainty tinggi.
    Tidak boleh confidence palsu.
    """

    def __init__(self, runtime_provider=None, workspace_provider=None):
        self._rp = runtime_provider
        self._wp = workspace_provider

    def evaluate(self, anomaly_type: str = "",
                 anomaly_detail: str = "",
                 severity: str = "information",
                 value: Optional[float] = None,
                 threshold: Optional[float] = None,
                 evidence: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None) -> DecisionProposal:
        """Evaluasi satu anomali/observasi → proposal keputusan.

        Args:
            anomaly_type: Tipe anomali (cpu_spike, memory_high, dll.)
            anomaly_detail: Detail tambahan
            severity: severity anomali
            value: Nilai terukur (opsional)
            threshold: Ambang batas (opsional)
            evidence: Evidence yang mendukung
            context: Data tambahan untuk keputusan

        Returns:
            DecisionProposal dengan confidence sesuai evidence.
        """
        ctx = context or {}
        ev = evidence or []
        evidence_count = len(ev)

        # Resolve policy berdasarkan tipe anomali
        if anomaly_type == "database_unavailable":
            return self._propose(
                decision="Restart database connection",
                reason="Database detected as unavailable",
                confidence=min(0.95, 0.5 + evidence_count * 0.1),
                evidence_count=evidence_count,
                evidence=ev,
                uncertainty="Check if database process is running" if evidence_count < 3 else "",
                missing_information=["Database process status"] if evidence_count < 2 else [],
            )
        elif anomaly_type == "disk_exhaustion":
            return self._propose(
                decision="Free up disk space",
                reason="Disk at {:.1f}% capacity — approaching exhaustion".format(value or 0),
                confidence=min(0.9, 0.4 + evidence_count * 0.1),
                evidence_count=evidence_count,
                evidence=ev,
                uncertainty="Unknown which files are consuming the most space" if evidence_count < 3 else "",
                missing_information=(["File-level disk usage scan"] if evidence_count < 2 else [])
                                 if value and value > 90 else [],
            )
        elif anomaly_type == "cpu_spike":
            return self._propose(
                decision="Investigate CPU spike",
                reason="CPU at {:.1f}% — abnormal for baseline operations".format(value or 0),
                confidence=min(0.85, 0.3 + evidence_count * 0.12),
                evidence_count=evidence_count,
                evidence=ev,
                uncertainty="Need to identify which process is consuming CPU" if evidence_count < 3 else "",
                missing_information=["Per-process CPU breakdown"] if evidence_count < 2 else [],
            )
        elif anomaly_type == "queue_growth":
            return self._propose(
                decision="Drain pending queue",
                reason="Queue depth: {} — growing faster than throughput".format(value or 0),
                confidence=min(0.9, 0.4 + evidence_count * 0.1),
                evidence_count=evidence_count,
                evidence=ev,
                uncertainty="Need throughput analysis to determine if this is transient" if evidence_count < 3 else "",
                missing_information=["Throughput trend analysis"] if evidence_count < 2 else [],
            )
        elif anomaly_type == "memory_high":
            return self._propose(
                decision="Investigate memory usage",
                reason="Memory at {:.1f}%".format(value or 0),
                confidence=min(0.85, 0.3 + evidence_count * 0.12),
                evidence_count=evidence_count,
                evidence=ev,
                uncertainty="Unknown if leak or normal allocation" if evidence_count < 3 else "",
                missing_information=["Per-process memory breakdown"] if evidence_count < 2 else [],
            )
        elif anomaly_type == "temp_accumulation":
            return self._propose(
                decision="Clean up temp files",
                reason="Temp file accumulation detected",
                confidence=min(0.8, 0.3 + evidence_count * 0.1),
                evidence_count=evidence_count,
                evidence=ev,
                uncertainty="Need to verify which temp files are safe to delete" if evidence_count < 2 else "",
                missing_information=[] if evidence_count > 1 else ["List of temp files and ages"],
            )
        elif anomaly_type == "cache_explosion":
            return self._propose(
                decision="Clean up cache",
                reason="Cache size exceeded operational threshold",
                confidence=min(0.8, 0.3 + evidence_count * 0.1),
                evidence_count=evidence_count,
                evidence=ev,
                uncertainty="Verify that cache cleanup does not affect active operations" if evidence_count < 2 else "",
                missing_information=["Active operations using cache"] if evidence_count < 2 else [],
            )

        # Unknown anomaly type — generic low confidence
        return self._propose(
            decision="Review anomaly",
            reason="{} detected".format(anomaly_type.replace("_", " ") if anomaly_type else "Unknown event"),
            confidence=0.3,
            evidence_count=evidence_count,
            evidence=ev,
            uncertainty="Anomaly type not recognized by policy framework",
            missing_information=["Structured anomaly analysis"] if evidence_count < 2 else [],
        )

    def evaluate_all(self, anomaly_detector=None,
                      runtime_provider=None,
                      workspace_provider=None) -> DecisionPackage:
        """Evaluasi semua anomali → semua proposal keputusan.

        Args:
            anomaly_detector: AnomalyDetector instance
            runtime_provider: RuntimeProvider instance (fallback)
            workspace_provider: WorkspaceProvider instance (fallback)

        Returns:
            DecisionPackage — semua proposal dari observasi ini.
        """
        rp = runtime_provider or self._rp
        wp = workspace_provider or self._wp
        proposals = []

        # Dari anomaly detector
        if anomaly_detector:
            anomalies = anomaly_detector.detect_all()
            for a in anomalies:
                proposal = self.evaluate(
                    anomaly_type=a.type,
                    anomaly_detail=a.detail or "",
                    severity=a.severity,
                    value=a.value,
                    threshold=a.threshold,
                    evidence=a.evidence,
                    context={"anomaly_type": a.type, "severity": a.severity},
                )
                proposals.append(proposal)

        # Dari runtime
        if rp:
            snap = rp.get_latest()
            if snap:
                # Recent restart — butuh observasi
                if snap.uptime_seconds < 300 and snap.uptime_seconds > 0:
                    proposals.append(self._propose(
                        decision="Monitor system stability after restart",
                        reason="System restarted {:.0f}s ago — waiting for stabilization".format(
                            snap.uptime_seconds
                        ),
                        confidence=0.6,
                        evidence_count=1,
                        evidence=["Uptime: {:.0f}s".format(snap.uptime_seconds)],
                        uncertainty="Too early to determine if restart resolved the underlying issue",
                        missing_information=["Pre-restart event analysis"],
                    ))

                # Queue growing
                if getattr(snap, 'queue_status', '') == 'growing':
                    proposals.append(self._propose(
                        decision="Scale up processing capacity",
                        reason="Queue is growing at current throughput rate",
                        confidence=0.65,
                        evidence_count=2,
                        evidence=["Queue status: growing", "Queue depth: {}".format(snap.queue_depth)],
                        uncertainty="Not sure if this is a temporary spike or sustained load",
                        missing_information=["Throughput trend (last 5 minutes)"],
                    ))

        # Sorting descending confidence
        proposals.sort(key=lambda p: p.confidence, reverse=True)

        return DecisionPackage(proposals=proposals)

    def _propose(self, decision: str, reason: str,
                 confidence: float, evidence_count: int,
                 evidence: List[str],
                 uncertainty: str = "",
                 missing_information: List[str] = None,
                 blocking_conditions: List[str] = None) -> DecisionProposal:
        """Internal — buat proposal dengan validasi confidence."""
        if missing_information is None:
            missing_information = []
        if blocking_conditions is None:
            blocking_conditions = []

        return DecisionProposal(
            decision=decision,
            reason=reason,
            confidence=max(0.0, min(1.0, confidence)),
            required_evidence=evidence,
            blocking_conditions=blocking_conditions,
            evidence_count=evidence_count,
            uncertainty=uncertainty,
            missing_information=missing_information,
        )
