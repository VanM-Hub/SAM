"""
OP-253 — Correlation Engine.

Connect related findings into correlated findings.

Built-in correlations:
  - approval_backlog + trust_degradation (approval macet → trust turun)
  - mission_failure + replay_degradation (mission gagal + replay buruk)
  - lock_contention + queue_stall (lock conflict + scheduler queue macet)
  - anomaly_cluster + high_telemetry (banyak anomaly + traffic tinggi)
  - notification_alert + failed_missions (notifikasi error + mission gagal)
  - low_trust + high_telemetry (trust turun + aktivitas mencurigakan)

Each correlation produces a single CorrelatedFinding with:
  - source finding IDs
  - combined severity (max of sources)
  - combined evidence
  - generated title + description
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class CorrelationDef:
    """Definition of a correlation between two or more finding types."""

    correlation_id: str
    title: str
    description: str
    source_types: Tuple[str, ...]
    combine_fn: str = "or"  # how to combine: "or" | "and"


@dataclass
class CorrelatedFinding:
    """
    A finding produced by correlating two or more source findings.

    Linked back to source finding IDs for traceability.
    """

    correlation_id: str
    source_finding_ids: List[str]
    title: str
    description: str
    severity: str  # "info" | "warning" | "critical"
    confidence: float
    evidence: List[Dict[str, Any]]
    affected_sources: List[str]
    recommended_actions: List[str]


# ── Engine ─────────────────────────────────────────────────────────


class CorrelationEngine:
    """
    Detects correlations between findings.

    Uses a registry of CorrelationDef to detect patterns.
    """

    def __init__(self):
        self._correlations: Dict[str, CorrelationDef] = {}
        self._last_correlated: List[CorrelatedFinding] = []
        self._register_defaults()

    # ── Public API ─────────────────────────────────────────────────

    @property
    def last_correlated(self) -> List[CorrelatedFinding]:
        return self._last_correlated

    @property
    def correlation_count(self) -> int:
        return len(self._correlations)

    def add_correlation(self, corr: CorrelationDef) -> None:
        self._correlations[corr.correlation_id] = corr

    def remove_correlation(self, correlation_id: str) -> bool:
        return self._correlations.pop(correlation_id, None) is not None

    def find_correlations(
        self, finding_ids: Dict[str, Dict[str, Any]]
    ) -> List[CorrelatedFinding]:
        """
        Given a dict of {finding_id: finding_data}, find correlated findings.

        finding_data should have keys: severity, confidence, evidence, title, etc.
        """
        results: List[CorrelatedFinding] = []

        for corr_id, corr_def in self._correlations.items():
            matched = self._match(corr_def, finding_ids)
            if matched:
                correlated = self._build_correlated(corr_def, matched)
                results.append(correlated)

        self._last_correlated = results
        return results

    def find_from_finding_list(
        self, findings: List[Dict[str, Any]]
    ) -> List[CorrelatedFinding]:
        """
        Convenience: accept list of finding dicts instead of dict-of-dicts.
        """
        finding_ids = {}
        for f in findings:
            fid = f.get("finding_id", f.get("id", "unknown"))
            finding_ids[fid] = f
        return self.find_correlations(finding_ids)

    # ── Internal ───────────────────────────────────────────────────

    def _register_defaults(self) -> None:
        """Register built-in correlations."""
        defaults = [
            CorrelationDef(
                correlation_id="approval_trust_cascade",
                title="Approval Backlog + Trust Degradation",
                description=(
                    "Pending approvals are high while trust scores are dropping. "
                    "This cascade suggests the approval bottleneck is eroding "
                    "system trust in mission_controller."
                ),
                source_types=("approval_backlog", "trust_degradation"),
            ),
            CorrelationDef(
                correlation_id="mission_replay_failure_chain",
                title="Mission Failure + Replay Degradation",
                description=(
                    "Mission failures coincide with poor replay success rates. "
                    "Failed missions may not be recoverable via replay."
                ),
                source_types=("mission_failure", "replay_degradation"),
            ),
            CorrelationDef(
                correlation_id="lock_queue_deadlock",
                title="Lock Contention + Queue Stall",
                description=(
                    "Lock contention and scheduler queue stall detected together. "
                    "Possible deadlock or resource starvation scenario."
                ),
                source_types=("lock_contention", "queue_stall"),
            ),
            CorrelationDef(
                correlation_id="anomaly_traffic_burst",
                title="Anomaly Cluster + High Telemetry",
                description=(
                    "Multiple anomalies coinciding with elevated event rate. "
                    "System may be under stress or attack pattern."
                ),
                source_types=("anomaly_cluster", "high_telemetry"),
            ),
            CorrelationDef(
                correlation_id="failure_notification_storm",
                title="Notification Alert + Mission Failures",
                description=(
                    "Error-level notifications paired with failed missions. "
                    "Indicates systemic issue rather than isolated failures."
                ),
                source_types=("notification_alert", "mission_failure"),
            ),
            CorrelationDef(
                correlation_id="trust_telemetry_anomaly",
                title="Low Trust + High Telemetry",
                description=(
                    "Trust is dropping while telemetry rates spike. "
                    "Suspicious activity or system degradation pattern."
                ),
                source_types=("trust_degradation", "high_telemetry"),
            ),
        ]
        for corr in defaults:
            self._correlations[corr.correlation_id] = corr

    def _match(
        self, corr_def: CorrelationDef, finding_ids: Dict[str, Dict[str, Any]]
    ) -> Optional[List[Tuple[str, Dict[str, Any]]]]:
        matched: List[Tuple[str, Dict[str, Any]]] = []
        for stype in corr_def.source_types:
            if stype in finding_ids:
                matched.append((stype, finding_ids[stype]))

        if corr_def.combine_fn == "and":
            return matched if len(matched) == len(corr_def.source_types) else None
        else:
            # "or" — at least one
            return matched if matched else None

    def _build_correlated(
        self,
        corr_def: CorrelationDef,
        matches: List[Tuple[str, Dict[str, Any]]],
    ) -> CorrelatedFinding:
        severities = {"info": 0, "warning": 1, "critical": 2}
        rev = {0: "info", 1: "warning", 2: "critical"}

        max_sev = max(
            (severities.get(m[1].get("severity", "info"), 0) for m in matches),
            default=0,
        )
        # Combined confidence: weighted average, capped
        total_conf = sum(
            m[1].get("confidence", 0.5) for m in matches
        )
        avg_conf = round(total_conf / len(matches), 2) if matches else 0.5

        # Combined evidence
        evidence: List[Dict[str, Any]] = []
        for stype, fdata in matches:
            src_evidence = fdata.get("evidence", [])
            for e in src_evidence:
                evidence.append({
                    **e,
                    "_source_finding": stype,
                })

        # Affected sources
        sources: List[str] = []
        for stype, fdata in matches:
            for r in fdata.get("affected_resources", []):
                if r not in sources:
                    sources.append(r)

        # Recommended actions
        actions: List[str] = []
        for stype, fdata in matches:
            for a in fdata.get("recommended_actions", []):
                if a not in actions:
                    actions.append(a)

        finding_ids_list = [m[0] for m in matches]

        return CorrelatedFinding(
            correlation_id=corr_def.correlation_id,
            source_finding_ids=finding_ids_list,
            title=corr_def.title,
            description=corr_def.description,
            severity=rev.get(max_sev, "info"),
            confidence=avg_conf,
            evidence=evidence,
            affected_sources=sources,
            recommended_actions=actions,
        )


# ── Convenience ────────────────────────────────────────────────────


def correlate_findings(
    findings: List[Dict[str, Any]]
) -> List[CorrelatedFinding]:
    """One-shot: correlate a list of finding dicts."""
    engine = CorrelationEngine()
    return engine.find_from_finding_list(findings)


def build_finding_dict(
    finding_id: str,
    severity: str = "info",
    confidence: float = 0.5,
    evidence: Optional[List[Dict[str, Any]]] = None,
    affected_resources: Optional[List[str]] = None,
    recommended_actions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a finding dict compatible with correlate_findings."""
    return {
        "finding_id": finding_id,
        "severity": severity,
        "confidence": confidence,
        "evidence": evidence or [],
        "affected_resources": affected_resources or [],
        "recommended_actions": recommended_actions or [],
    }
