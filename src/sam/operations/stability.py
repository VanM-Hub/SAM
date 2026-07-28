"""
OP-112 — Decision Stability Test.

Uji sensitivitas: perubahan kecil pada input → seberapa besar perubahan output?

Contoh: CPU 60% → 61% → 62% → 63% → 64%
Pastikan SAM tidak berubah total hanya karena perubahan kecil.

Output: DecisionStabilityReport dengan threshold configurable.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable


@dataclass
class DecisionChange:
    """Catatan perubahan untuk satu langkah input."""
    step_a: Any          # Input value at step A
    step_b: Any          # Input value at step B
    input_delta: float   # Perubahan input (abs)
    recommendation_changed: bool = False
    score_changed: bool = False
    score_delta: float = 0.0
    confidence_changed: bool = False
    confidence_delta: float = 0.0
    risk_changed: bool = False
    explanation_changed: bool = False
    alternatives_changed: bool = False
    execution_changed: bool = False

    def total_changes(self) -> int:
        c = 0
        if self.recommendation_changed: c += 1
        if self.score_changed: c += 1
        if self.confidence_changed: c += 1
        if self.risk_changed: c += 1
        if self.explanation_changed: c += 1
        if self.alternatives_changed: c += 1
        if self.execution_changed: c += 1
        return c

    def is_acceptable(self, max_changes: int = 2) -> bool:
        """Apakah perubahan ini wajar? Maks 2 field berubah untuk delta kecil."""
        return self.total_changes() <= max_changes

    def to_dict(self) -> dict:
        return {
            "input_delta": self.input_delta,
            "recommendation_changed": self.recommendation_changed,
            "score_delta": self.score_delta,
            "confidence_delta": self.confidence_delta,
            "risk_changed": self.risk_changed,
            "total_changes": self.total_changes(),
        }


@dataclass
class DecisionStabilityReport:
    """Laporan stabilitas untuk satu set input bertahap."""
    test_name: str
    input_label: str                     # "cpu_percent"
    input_values: List[float]            # [60, 61, 62, 63, 64]
    changes: List[DecisionChange]        # Perubahan per langkah
    total_steps: int = 0
    total_changes: int = 0
    max_changes_in_step: int = 0
    average_changes_per_step: float = 0.0
    unstable_steps: int = 0              # Steps dengan >2 changes
    acceptable: bool = True
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "input_label": self.input_label,
            "input_range": [min(self.input_values), max(self.input_values)] if self.input_values else [],
            "total_steps": self.total_steps,
            "total_changes": self.total_changes,
            "average_changes_per_step": self.average_changes_per_step,
            "unstable_steps": self.unstable_steps,
            "acceptable": self.acceptable,
            "reason": self.reason,
        }


class StabilityConfig:
    """Konfigurasi threshold stabilitas."""
    def __init__(self, max_field_change: int = 2, max_score_jump: float = 10.0):
        self.max_field_change = max_field_change   # Max field berubah per step
        self.max_score_jump = max_score_jump       # Max selisih score yang wajar


class StabilityTester:
    """Test stabilitas untuk input incremental.

    Cara pakai:
      tester = StabilityTester()
      tester.run(
          test_name="CPU Sensitivity",
          input_label="cpu_percent",
          input_values=[60, 61, 62, 63, 64],
          decision_fn=lambda cpu: generate_decision(cpu),
      )
      report = tester.report()
    """

    def __init__(self, config: Optional[StabilityConfig] = None):
        self.config = config or StabilityConfig()
        self._last_report: Optional[DecisionStabilityReport] = None

    def run(self, test_name: str, input_label: str,
            input_values: List[float],
            decision_fn: Callable) -> DecisionStabilityReport:
        """Jalankan test stabilitas.

        Args:
            test_name: Nama test
            input_label: Label variabel yang diubah
            input_values: Nilai input incremental
            decision_fn: Fungsi yang menerima float → DecisionSnapshot

        Returns:
            DecisionStabilityReport
        """
        if len(input_values) < 2:
            empty = DecisionStabilityReport(
                test_name=test_name, input_label=input_label, input_values=input_values,
                changes=[], acceptable=True, reason="Need at least 2 values",
            )
            self._last_report = empty
            return empty

        from .consistency import DecisionSnapshot   # lazy import

        # Generate decisions
        decisions = []
        for val in input_values:
            dp = decision_fn(val)
            if isinstance(dp, DecisionSnapshot):
                decisions.append(dp)
            else:
                snap = DecisionSnapshot.from_decision_package(dp)
                decisions.append(snap)

        changes = []
        total_change_count = 0
        max_changes = 0
        unstable = 0

        for i in range(1, len(decisions)):
            a, b = decisions[i - 1], decisions[i]
            delta = abs(input_values[i] - input_values[i - 1])
            score_delta = abs(b.score - a.score)
            conf_delta = abs(b.confidence - a.confidence)

            rec_changed = a.recommendation.strip().lower() != b.recommendation.strip().lower()
            score_changed = score_delta >= 0.5
            conf_changed = conf_delta >= 0.01
            risk_changed = a.risk_level != b.risk_level
            alt_set_a = set(t.lower().strip() for t in a.alternatives)
            alt_set_b = set(t.lower().strip() for t in b.alternatives)
            alts_changed = alt_set_a != alt_set_b
            ev_set_a = set(e.lower().strip() for e in a.explanation_evidence)
            ev_set_b = set(e.lower().strip() for e in b.explanation_evidence)
            expl_changed = ev_set_a != ev_set_b
            act_set_a = set(x.lower().strip() for x in a.execution_plan_actions)
            act_set_b = set(x.lower().strip() for x in b.execution_plan_actions)
            exec_changed = act_set_a != act_set_b

            dc = DecisionChange(
                step_a=input_values[i - 1], step_b=input_values[i],
                input_delta=delta,
                recommendation_changed=rec_changed,
                score_changed=score_changed,
                score_delta=score_delta,
                confidence_changed=conf_changed,
                confidence_delta=conf_delta,
                risk_changed=risk_changed,
                explanation_changed=expl_changed,
                alternatives_changed=alts_changed,
                execution_changed=exec_changed,
            )
            changes.append(dc)

            tc = dc.total_changes()
            total_change_count += tc
            if tc > max_changes:
                max_changes = tc
            if not dc.is_acceptable(self.config.max_field_change):
                unstable += 1

        avg_changes = round(total_change_count / max(1, len(changes)), 2)

        # Apakah acceptable?
        acceptable = True
        reasons = []

        if unstable > 0:
            acceptable = False
            reasons.append("{} unstable steps (>{})".format(unstable, self.config.max_field_change))

        # Periksa score jump
        for dc in changes:
            if dc.score_delta > self.config.max_score_jump:
                acceptable = False
                reasons.append("Score jump >{} (max={:.1f})".format(
                    self.config.max_score_jump, dc.score_delta))
                break

        if not reasons:
            reason = "Stable: {} steps, avg {:.2f} changes/step, max {} changes/step".format(
                len(changes), avg_changes, max_changes)
        else:
            reason = "Unstable: {}".format("; ".join(reasons))

        report = DecisionStabilityReport(
            test_name=test_name,
            input_label=input_label,
            input_values=input_values,
            changes=changes,
            total_steps=len(changes),
            total_changes=total_change_count,
            max_changes_in_step=max_changes,
            average_changes_per_step=avg_changes,
            unstable_steps=unstable,
            acceptable=acceptable,
            reason=reason,
        )
        self._last_report = report
        return report

    @property
    def last_report(self) -> Optional[DecisionStabilityReport]:
        return self._last_report
