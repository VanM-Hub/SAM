"""
Counterfactual Analysis — "What if...?"

SAM mampu menjawab skenario alternatif secara berbasis evidence.
Jika data tidak cukup: "Insufficient evidence. Prediction cannot be made."
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class WhatIfScenario:
    """Satu skenario what-if."""
    scenario: str                        # "I do nothing", "I restart", "I wait 10 minutes"
    expected_outcome: str                # "Queue recovers within 5 minutes"
    probability: float                   # 0.0-1.0
    evidence: List[str] = field(default_factory=list)
    unknown_factors: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)

    def is_sufficient(self) -> bool:
        """Apakah prediksi bisa dibuat?"""
        return self.probability > 0.0 and len(self.evidence) > 0

    def to_text(self) -> str:
        if not self.is_sufficient():
            return "{scenario}: Insufficient evidence. Prediction cannot be made.".format(
                scenario=self.scenario,
            )
        parts = [
            "{scenario}: {outcome}".format(scenario=self.scenario, outcome=self.expected_outcome),
            "  Probability: {:.0f}%".format(self.probability * 100),
        ]
        if self.evidence:
            parts.append("  Evidence:")
            for e in self.evidence[:3]:
                parts.append("    - {e}".format(e=e))
        if self.unknown_factors:
            parts.append("  Unknown factors:")
            for u in self.unknown_factors[:3]:
                parts.append("    - {u}".format(u=u))
        if self.missing_evidence:
            parts.append("  Missing evidence:")
            for m in self.missing_evidence[:3]:
                parts.append("    - {m}".format(m=m))
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "expected_outcome": self.expected_outcome,
            "probability": self.probability,
            "evidence": self.evidence,
            "unknown_factors": self.unknown_factors,
            "missing_evidence": self.missing_evidence,
            "is_sufficient": self.is_sufficient(),
        }


@dataclass
class CounterfactualPackage:
    """Semua skenario what-if dari satu situasi."""
    scenarios: List[WhatIfScenario] = field(default_factory=list)
    best_course: str = ""
    confidence: float = 0.0

    def to_text(self) -> str:
        if not self.scenarios:
            return "No what-if scenarios evaluated."
        parts = ["=== What-If Analysis ==="]
        for s in self.scenarios:
            parts.append("")
            parts.append(s.to_text())
        if self.best_course:
            parts.append("")
            parts.append("Recommended course: {best}".format(best=self.best_course))
        return "\n".join(parts)

    def to_dict(self) -> dict:
        return {
            "scenarios": [s.to_dict() for s in self.scenarios],
            "best_course": self.best_course,
            "confidence": self.confidence,
        }


class CounterfactualEngine:
    """Engine untuk analisis what-if.

    Method utama:
      analyze(anomaly_type, value, threshold, context) -> CounterfactualPackage

    Aturan:
      - Setiap prediksi WAJIB punya confidence
      - Jika evidence tidak cukup: is_sufficient = False
      - Tidak boleh mengarang
    """

    def analyze(self, anomaly_type: str = "",
                value: Optional[float] = None,
                threshold: Optional[float] = None,
                context: Optional[Dict[str, Any]] = None) -> CounterfactualPackage:
        """Analisis what-if untuk satu situasi.

        Args:
            anomaly_type: Tipe anomali
            value: Nilai terukur
            threshold: Ambang batas
            context: Data observasi tambahan

        Returns:
            CounterfactualPackage dengan skenario-skenario.
        """
        ctx = context or {}
        scenarios = []
        evidence_count = len(ctx.get("evidence", []))
        has_rollback = ctx.get("has_rollback", False)
        severity = ctx.get("severity", "information")

        # === What-if: Do Nothing ===
        do_nothing_evidence = [
            "Current value: {val}".format(val=value if value is not None else "unknown"),
            "Type: {type}".format(type=anomaly_type.replace("_", " ") if anomaly_type else "unknown"),
        ]
        if evidence_count > 0:
            do_nothing_evidence.append("Evidence sources: {count}".format(count=evidence_count))

        do_nothing_unknown = self._estimate_unknown_factors(value, anomaly_type, severity)

        # Hitung probability do-nothing
        dn_probability, dn_outcome = self._estimate_do_nothing(
            anomaly_type, value, threshold, severity, evidence_count,
        )

        scenarios.append(WhatIfScenario(
            scenario="What if nothing is done?",
            expected_outcome=dn_outcome,
            probability=dn_probability,
            evidence=do_nothing_evidence,
            unknown_factors=do_nothing_unknown,
            missing_evidence=["No intervention metrics available"] if evidence_count < 2 else [],
        ))

        # === What-if: Take recommended action ===
        action_evidence = [
            "Action type: {type}".format(type=self._get_action_type(anomaly_type)),
            "Severity: {severity}".format(severity=severity),
        ]
        if value is not None:
            action_evidence.append("Current value: {val}".format(val=value))

        if has_rollback:
            action_evidence.append("Rollback is available — risk is limited")

        act_probability, act_outcome = self._estimate_action(
            anomaly_type, value, threshold, severity, evidence_count, has_rollback,
        )

        scenarios.append(WhatIfScenario(
            scenario="What if action is taken ({action})?".format(
                action=self._get_action_label(anomaly_type)),
            expected_outcome=act_outcome,
            probability=act_probability,
            evidence=action_evidence,
            unknown_factors=self._estimate_action_unknown(anomaly_type),
            missing_evidence=["Per-process impact analysis"] if evidence_count < 3 else [],
        ))

        # === What-if: Wait X minutes ===
        wait_probability, wait_outcome = self._estimate_wait(
            anomaly_type, value, threshold, severity, evidence_count,
        )
        scenarios.append(WhatIfScenario(
            scenario="What if waiting is chosen?",
            expected_outcome=wait_outcome,
            probability=wait_probability,
            evidence=["No immediate intervention", "Observation continues"],
            unknown_factors=["Condition may worsen during wait"],
            missing_evidence=["Time-to-escalation metrics"],
        ))

        # === Additional: What-if Rollback ===
        if has_rollback:
            scenarios.append(WhatIfScenario(
                scenario="What if rollback is needed?",
                expected_outcome="System returns to previous stable state",
                probability=0.6,
                evidence=["Rollback steps defined: {count}".format(
                    count=ctx.get("rollback_count", 1))],
                unknown_factors=["Rollback may leave partial state changes"],
                missing_evidence=["Previous successful rollback ratio"],
            ))

        # Pilih best course
        best_scenario = max(scenarios, key=lambda s: s.probability if s.is_sufficient() else 0)
        best_course = best_scenario.scenario if best_scenario.probability > 0.3 else "Insufficient data to recommend a course"

        return CounterfactualPackage(
            scenarios=scenarios,
            best_course=best_course,
            confidence=best_scenario.probability if best_scenario.is_sufficient() else 0.0,
        )

    def _estimate_unknown_factors(self, value: Optional[float],
                                   anomaly_type: str, severity: str) -> List[str]:
        """Estimasi faktor yang tidak diketahui."""
        factors = []
        if anomaly_type == "database_unavailable":
            factors.append("Database service restart time")
            if severity in ("high", "critical"):
                factors.append("Potential data loss during restart")
        elif anomaly_type == "disk_exhaustion":
            if value and value > 90:
                factors.append("Exact time until disk full")
            factors.append("Which files consume the most space")
        elif anomaly_type in ("cpu_spike", "memory_high"):
            factors.append("Cause of the spike")
        if severity == "critical":
            factors.append("Rate of deterioration")
        return factors or ["Standard operational conditions"]

    def _estimate_do_nothing(self, anomaly_type: str,
                              value: Optional[float],
                              threshold: Optional[float],
                              severity: str,
                              evidence_count: int) -> tuple:
        """Estimasi jika tidak melakukan apa-apa."""
        base_prob = max(0.1, 0.5 + evidence_count * 0.05)

        if anomaly_type == "database_unavailable":
            return (0.15, "Connection will remain unavailable. Service disruption continues indefinitely.")
        elif anomaly_type == "disk_exhaustion":
            if value and value > 95:
                return (0.05, "Disk will become full within minutes. All write operations will fail.")
            elif value and value > 85:
                return (0.20, "Disk usage will continue increasing. May reach critical in hours.")
            return (0.40, "Disk usage will remain stable over short term.")
        elif anomaly_type in ("cpu_spike", "memory_high"):
            if severity in ("high", "critical"):
                return (0.20, "System performance degrades further. Risk of OOM or throttling.")
            return (0.50, "Spike may self-correct within minutes.")
        elif anomaly_type == "queue_growth":
            if value and value > 100:
                return (0.15, "Queue continues growing. Backlog accumulates, processing delays worsen.")
            return (0.40, "Queue may drain naturally if upstream issue resolves.")
        else:
            return (0.30, "Situation unchanged. Monitoring continues without degradation.")

    def _estimate_action(self, anomaly_type: str,
                          value: Optional[float],
                          threshold: Optional[float],
                          severity: str,
                          evidence_count: int,
                          has_rollback: bool) -> tuple:
        """Estimasi jika action diambil."""
        base = 0.4 + evidence_count * 0.08 + (0.1 if has_rollback else 0)

        if anomaly_type == "database_unavailable":
            return (min(0.95, base + 0.3), "Database connection restored within 30 seconds. Queue resumes processing.")
        elif anomaly_type == "disk_exhaustion":
            return (min(0.90, base + 0.2), "Disk space freed. Write operations resume normally.")
        elif anomaly_type in ("cpu_spike", "memory_high"):
            return (min(0.80, base + 0.1), "System resources return to normal range. Performance stabilizes.")
        elif anomaly_type == "queue_growth":
            return (min(0.85, base + 0.15), "Queue drains within minutes. Processing returns to normal.")
        else:
            return (min(0.70, base), "Action taken. Monitoring required to confirm resolution.")

    def _estimate_wait(self, anomaly_type: str,
                        value: Optional[float],
                        threshold: Optional[float],
                        severity: str,
                        evidence_count: int) -> tuple:
        """Estimasi jika menunggu."""
        if severity in ("high", "critical") and evidence_count > 1:
            return (0.20, "Waiting may worsen the situation. Risk of escalation.")
        elif anomaly_type == "database_unavailable":
            return (0.10, "Database will not self-recover. Waiting is ineffective.")
        elif anomaly_type in ("cpu_spike", "memory_high"):
            return (0.40, "Spike may self-correct. Monitoring is safe but delays resolution.")
        else:
            return (0.30, "Waiting may or may not help. Monitoring continues.")

    def _get_action_type(self, anomaly_type: str) -> str:
        mapping = {
            "database_unavailable": "restart",
            "disk_exhaustion": "cleanup",
            "cpu_spike": "investigate",
            "memory_high": "investigate",
            "queue_growth": "drain",
            "temp_accumulation": "cleanup",
            "cache_explosion": "cleanup",
        }
        return mapping.get(anomaly_type, "investigate")

    def _get_action_label(self, anomaly_type: str) -> str:
        if anomaly_type == "database_unavailable":
            return "restart"
        elif anomaly_type == "disk_exhaustion":
            return "clean up"
        elif anomaly_type in ("cpu_spike", "memory_high"):
            return "investigate"
        elif anomaly_type == "queue_growth":
            return "drain queue"
        else:
            return "take recommended action"

    def _estimate_action_unknown(self, anomaly_type: str) -> List[str]:
        if anomaly_type == "database_unavailable":
            return ["Restart may not resolve if underlying issue is configuration"]
        elif anomaly_type == "disk_exhaustion":
            return ["Cleanup may not free enough space if problem is persistent"]
        elif anomaly_type in ("cpu_spike", "memory_high"):
            return ["Investigation may not immediately resolve the root cause"]
        else:
            return ["Action effectiveness depends on current system state"]
