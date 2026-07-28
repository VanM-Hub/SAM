"""
OP-115 — Decision Drift Detector.

Bandingkan keputusan hari ini vs keputusan minggu lalu.
Deteksi drift dalam recommendation, policy, evidence, confidence.
Jelaskan mengapa jika berubah.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


@dataclass
class DriftField:
    """Satu field yang mengalami drift."""
    field: str
    drifted: bool
    old_value: str = ""
    new_value: str = ""
    delta: float = 0.0
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "drifted": self.drifted,
            "delta": self.delta,
            "explanation": self.explanation,
        }


@dataclass
class DecisionDriftReport:
    """Laporan drift untuk satu keputusan."""
    decision_title: str
    old_snapshot_id: str
    new_snapshot_id: str

    # Changes
    recommendation_drift: DriftField = field(default_factory=lambda: DriftField("recommendation", False))
    policy_drift: DriftField = field(default_factory=lambda: DriftField("policy", False))
    evidence_drift: DriftField = field(default_factory=lambda: DriftField("evidence", False))
    confidence_drift: DriftField = field(default_factory=lambda: DriftField("confidence", False))
    score_drift: DriftField = field(default_factory=lambda: DriftField("score", False))
    risk_drift: DriftField = field(default_factory=lambda: DriftField("risk", False))

    # Aggregate
    drifted_fields: int = 0
    total_fields: int = 6
    drift_percentage: float = 0.0
    has_drift: bool = False

    def to_dict(self) -> dict:
        return {
            "decision_title": self.decision_title,
            "drifted_fields": self.drifted_fields,
            "drift_percentage": self.drift_percentage,
            "has_drift": self.has_drift,
            "fields": [
                self.recommendation_drift.to_dict(),
                self.policy_drift.to_dict(),
                self.evidence_drift.to_dict(),
                self.confidence_drift.to_dict(),
                self.score_drift.to_dict(),
                self.risk_drift.to_dict(),
            ],
        }


@dataclass
class DriftSnapshot:
    """Snapshot untuk drift detection."""
    decision_title: str
    recommendation: str
    policy_version: str
    evidence: List[str]
    confidence: float
    score: float
    risk: str


@dataclass
class DriftPackage:
    """Kumpulan drift reports."""
    reports: List[DecisionDriftReport] = field(default_factory=list)
    total: int = 0
    drifted: int = 0
    average_drift: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "drifted": self.drifted,
            "average_drift": self.average_drift,
        }

    def to_text(self) -> str:
        return "Drift: {}/{} decisions drifted ({:.1f}% avg)".format(
            self.drifted, self.total, self.average_drift)


class DriftDetector:
    """Deteksi drift antara dua snapshot keputusan.

    Method:
      detect(old_snap, new_snap, old_id, new_id) -> DecisionDriftReport
      detect_batch(pairs) -> DriftPackage
    """

    def detect(self, old_snap: DriftSnapshot, new_snap: DriftSnapshot,
               old_id: str = "", new_id: str = "") -> DecisionDriftReport:
        """Deteksi drift.

        Args:
            old_snap: Snapshot lama (minggu lalu)
            new_snap: Snapshot baru (hari ini)
            old_id: ID snapshot lama
            new_id: ID snapshot baru

        Returns:
            DecisionDriftReport
        """
        fields: List[DriftField] = []
        drifted_count = 0

        # 1. Recommendation drift
        rec_drifted = old_snap.recommendation.strip().lower() != new_snap.recommendation.strip().lower()
        rec_expl = ""
        if rec_drifted:
            rec_expl = "Recommendation changed: '{}' → '{}'".format(
                old_snap.recommendation[:30], new_snap.recommendation[:30])
        rec_field = DriftField("recommendation", rec_drifted,
                               old_snap.recommendation, new_snap.recommendation,
                               explanation=rec_expl)
        if rec_drifted: drifted_count += 1
        fields.append(rec_field)

        # 2. Policy version drift
        pol_drifted = old_snap.policy_version != new_snap.policy_version
        pol_expl = ""
        if pol_drifted:
            pol_expl = "Policy version: {} → {}".format(old_snap.policy_version, new_snap.policy_version)
        pol_field = DriftField("policy", pol_drifted,
                               old_snap.policy_version, new_snap.policy_version,
                               explanation=pol_expl)
        if pol_drifted: drifted_count += 1
        fields.append(pol_field)

        # 3. Evidence drift
        ev_old_set = set(e.lower().strip() for e in old_snap.evidence)
        ev_new_set = set(e.lower().strip() for e in new_snap.evidence)
        ev_drifted = ev_old_set != ev_new_set
        ev_expl = ""
        if ev_drifted:
            only_old = ev_old_set - ev_new_set
            only_new = ev_new_set - ev_old_set
            parts = []
            if only_old:
                parts.append("removed: {}".format(", ".join(list(only_old)[:3])))
            if only_new:
                parts.append("added: {}".format(", ".join(list(only_new)[:3])))
            ev_expl = "; ".join(parts)
        ev_field = DriftField("evidence", ev_drifted,
                              str(len(ev_old_set)) + " items", str(len(ev_new_set)) + " items",
                              delta=float(abs(len(ev_old_set) - len(ev_new_set))),
                              explanation=ev_expl)
        if ev_drifted: drifted_count += 1
        fields.append(ev_field)

        # 4. Confidence drift
        conf_delta = abs(old_snap.confidence - new_snap.confidence)
        conf_drifted = conf_delta > 0.01
        conf_expl = ""
        if conf_drifted:
            direction = "increased" if new_snap.confidence > old_snap.confidence else "decreased"
            conf_expl = "Confidence {} by {:.0f}%".format(direction, conf_delta * 100)
        conf_field = DriftField("confidence", conf_drifted,
                                "{:.2f}".format(old_snap.confidence),
                                "{:.2f}".format(new_snap.confidence),
                                delta=round(conf_delta, 4), explanation=conf_expl)
        if conf_drifted: drifted_count += 1
        fields.append(conf_field)

        # 5. Score drift
        score_delta = abs(old_snap.score - new_snap.score)
        score_drifted = score_delta > 0.5
        score_expl = ""
        if score_drifted:
            direction = "increased" if new_snap.score > old_snap.score else "decreased"
            score_expl = "Score {} by {:.1f}".format(direction, score_delta)
        score_field = DriftField("score", score_drifted,
                                 "{:.1f}".format(old_snap.score),
                                 "{:.1f}".format(new_snap.score),
                                 delta=round(score_delta, 1), explanation=score_expl)
        if score_drifted: drifted_count += 1
        fields.append(score_field)

        # 6. Risk drift
        risk_drifted = old_snap.risk != new_snap.risk
        risk_expl = ""
        if risk_drifted:
            severity = "increased" if new_snap.risk > old_snap.risk else "decreased"
            risk_expl = "Risk {}: {} → {}".format(severity, old_snap.risk, new_snap.risk)
        risk_field = DriftField("risk", risk_drifted,
                                old_snap.risk, new_snap.risk, explanation=risk_expl)
        if risk_drifted: drifted_count += 1
        fields.append(risk_field)

        drift_pct = round((drifted_count / 6) * 100, 1)

        return DecisionDriftReport(
            decision_title=old_snap.decision_title,
            old_snapshot_id=old_id,
            new_snapshot_id=new_id,
            recommendation_drift=rec_field,
            policy_drift=pol_field,
            evidence_drift=ev_field,
            confidence_drift=conf_field,
            score_drift=score_field,
            risk_drift=risk_field,
            drifted_fields=drifted_count,
            drift_percentage=drift_pct,
            has_drift=drifted_count > 0,
        )

    def detect_batch(self, pairs: List[Tuple[DriftSnapshot, DriftSnapshot, str, str]]) -> DriftPackage:
        """Deteksi drift batch."""
        reports = []
        for old_snap, new_snap, old_id, new_id in pairs:
            reports.append(self.detect(old_snap, new_snap, old_id, new_id))

        total = len(reports)
        drifted = sum(1 for r in reports if r.has_drift)
        avg_drift = round(sum(r.drift_percentage for r in reports) / max(1, total), 1) if total else 0.0

        return DriftPackage(
            reports=reports,
            total=total,
            drifted=drifted,
            average_drift=avg_drift,
        )
