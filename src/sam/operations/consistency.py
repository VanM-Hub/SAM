"""
OP-111 — Decision Consistency Framework.

Mengukur apakah dua kondisi identik menghasilkan keputusan identik.
Semua perbandingan deterministik — tanpa LLM.

Membandingkan:
  - Recommendation title & content
  - Score
  - Confidence
  - Alternatives (set of titles)
  - Explanation (evidence, assumptions)
  - Risk level
  - Impact severity
  - Verification plan type
  - Execution plan actions
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum


class ConsistencyLevel(Enum):
    """Level konsistensi antara dua keputusan."""
    IDENTICAL = "identical"         # 100% — semuanya cocok
    MINOR = "minor"                 # >90% — beda tipis, score delta kecil
    SIGNIFICANT = "significant"     # >70% — beberapa perbedaan
    MAJOR = "major"                 # >50% — perbedaan substansial
    DIFFERENT = "different"         # <=50% — keputusan berbeda total
    UNKNOWN = "unknown"             # Data tidak cukup


@dataclass
class FieldComparison:
    """Perbandingan satu field."""
    field: str
    match: bool
    value_a: Any = None
    value_b: Any = None
    delta: float = 0.0  # numeric delta jika relevan

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "match": self.match,
            "delta": self.delta,
        }


@dataclass
class DecisionConsistencyResult:
    """Hasil perbandingan dua keputusan."""
    # Identity
    decision_title_a: str
    decision_title_b: str
    observation_hash_a: str = ""
    observation_hash_b: str = ""

    # Field-by-field
    same_decision: bool = False           # Rekomendasi utama cocok?
    same_score: bool = False
    score_delta: float = 0.0
    same_confidence: bool = False
    confidence_delta: float = 0.0
    same_explanation: bool = False
    same_alternatives: bool = False
    same_execution_plan: bool = False
    same_risk: bool = False
    same_impact: bool = False
    same_verification: bool = False

    # Aggregate
    field_comparisons: List[FieldComparison] = field(default_factory=list)
    total_fields: int = 0
    matched_fields: int = 0
    consistency_percentage: float = 0.0
    level: str = "unknown"

    def to_dict(self) -> dict:
        return {
            "decision_a": self.decision_title_a,
            "decision_b": self.decision_title_b,
            "same_decision": self.same_decision,
            "consistency_percentage": self.consistency_percentage,
            "level": self.level,
            "matched_fields": self.matched_fields,
            "total_fields": self.total_fields,
            "fields": [f.to_dict() for f in self.field_comparisons],
        }


@dataclass
class DecisionSnapshot:
    """Snapshot satu keputusan untuk perbandingan."""
    decision_title: str
    recommendation: str              # Nama rekomendasi utama
    score: float                     # 0-100
    confidence: float                # 0.0-1.0
    risk_level: str                  # SAFE/LOW/MEDIUM/HIGH/CRITICAL
    impact_severity: str             # HIGH/MEDIUM/LOW/CRITICAL/NONE
    verification_plan_type: str      # simple/standard/full
    alternatives: List[str]          # Titles
    explanation_evidence: List[str]  # Evidence keys
    explanation_assumptions: List[str]
    execution_plan_actions: List[str]
    observation_hash: str = ""       # Hash dari snapshot observasi

    @classmethod
    def from_decision_package(cls, dp: Any, obs_hash: str = "") -> "DecisionSnapshot":
        """Buat snap dari DecisionPackage."""
        score = 0.0
        confidence = 0.0
        if hasattr(dp, 'score'):
            score = dp.score
        if hasattr(dp, 'confidence'):
            confidence = dp.confidence

        risk = "UNKNOWN"
        if hasattr(dp, 'risk_level'):
            risk = dp.risk_level
        elif hasattr(dp, 'risk'):
            risk = str(dp.risk)

        alt_titles = []
        if hasattr(dp, 'alternatives') and dp.alternatives:
            alt_titles = [getattr(a, 'title', str(a)[:30]) for a in dp.alternatives]

        evidence_keys = []
        if hasattr(dp, 'explanation'):
            expl = dp.explanation
            if hasattr(expl, 'evidence_keys'):
                evidence_keys = expl.evidence_keys
            elif hasattr(expl, 'evidence') and isinstance(expl.evidence, list):
                evidence_keys = [str(e)[:30] for e in expl.evidence]

        actions = []
        if hasattr(dp, 'execution_plan'):
            plan = dp.execution_plan
            if hasattr(plan, 'actions'):
                actions = [getattr(a, 'title', str(a)[:30]) for a in plan.actions]

        return cls(
            decision_title=getattr(dp, 'title', getattr(dp, 'decision_title', str(dp)[:30])),
            recommendation=getattr(dp, 'recommendation', str(dp)[:30]),
            score=score,
            confidence=confidence,
            risk_level=risk,
            impact_severity=getattr(dp, 'impact_severity', "UNKNOWN"),
            verification_plan_type=getattr(dp, 'verification_plan_type', "standard"),
            alternatives=alt_titles,
            explanation_evidence=evidence_keys,
            explanation_assumptions=[],
            execution_plan_actions=actions,
            observation_hash=obs_hash,
        )


class ConsistencyEngine:
    """Engine untuk membandingkan dua keputusan.

    Method utama:
      compare(snapshot_a, snapshot_b) -> DecisionConsistencyResult
      compare_list(snapshots) -> List[DecisionConsistencyResult]
      aggregate_report(results) -> dict

    Semua deterministik — tanpa LLM.
    """

    def compare(self, snap_a: DecisionSnapshot,
                snap_b: DecisionSnapshot) -> DecisionConsistencyResult:
        """Bandingkan dua snapshot.

        Args:
            snap_a: Snapshot keputusan A
            snap_b: Snapshot keputusan B

        Returns:
            DecisionConsistencyResult
        """
        comparisons: List[FieldComparison] = []
        matched = 0
        total = 0

        # 1. Recommendation
        total += 1
        same_rec = snap_a.recommendation.strip().lower() == snap_b.recommendation.strip().lower()
        if same_rec:
            matched += 1
        comparisons.append(FieldComparison(
            "recommendation", same_rec, snap_a.recommendation, snap_b.recommendation,
        ))

        # 2. Score
        total += 1
        score_delta = abs(snap_a.score - snap_b.score)
        same_score = score_delta < 0.5
        if same_score:
            matched += 1
        comparisons.append(FieldComparison(
            "score", same_score, snap_a.score, snap_b.score, score_delta,
        ))

        # 3. Confidence
        total += 1
        conf_delta = abs(snap_a.confidence - snap_b.confidence)
        same_conf = conf_delta < 0.01
        if same_conf:
            matched += 1
        comparisons.append(FieldComparison(
            "confidence", same_conf, snap_a.confidence, snap_b.confidence, conf_delta,
        ))

        # 4. Risk level
        total += 1
        same_risk = snap_a.risk_level == snap_b.risk_level
        if same_risk:
            matched += 1
        comparisons.append(FieldComparison("risk", same_risk, snap_a.risk_level, snap_b.risk_level))

        # 5. Impact severity
        total += 1
        same_impact = snap_a.impact_severity == snap_b.impact_severity
        if same_impact:
            matched += 1
        comparisons.append(FieldComparison(
            "impact", same_impact, snap_a.impact_severity, snap_b.impact_severity,
        ))

        # 6. Verification plan
        total += 1
        same_verify = snap_a.verification_plan_type == snap_b.verification_plan_type
        if same_verify:
            matched += 1
        comparisons.append(FieldComparison(
            "verification", same_verify,
            snap_a.verification_plan_type, snap_b.verification_plan_type,
        ))

        # 7. Alternatives (set comparison)
        total += 1
        set_a = set(a.lower().strip() for a in snap_a.alternatives)
        set_b = set(b.lower().strip() for b in snap_b.alternatives)
        same_alts = set_a == set_b
        if same_alts:
            matched += 1
        comparisons.append(FieldComparison(
            "alternatives", same_alts,
            len(set_a), len(set_b), float(abs(len(set_a) - len(set_b))),
        ))

        # 8. Explanation evidence (set comparison)
        total += 1
        ev_set_a = set(e.lower().strip() for e in snap_a.explanation_evidence)
        ev_set_b = set(e.lower().strip() for e in snap_b.explanation_evidence)
        same_evidence = ev_set_a == ev_set_b
        if same_evidence:
            matched += 1
        comparisons.append(FieldComparison(
            "explanation_evidence", same_evidence,
            len(ev_set_a), len(ev_set_b),
        ))

        # 9. Execution plan actions (set comparison)
        total += 1
        act_set_a = set(a.lower().strip() for a in snap_a.execution_plan_actions)
        act_set_b = set(b.lower().strip() for b in snap_b.execution_plan_actions)
        same_actions = act_set_a == act_set_b
        if same_actions:
            matched += 1
        comparisons.append(FieldComparison(
            "execution_plan", same_actions, len(act_set_a), len(act_set_b),
        ))

        # Consistency percentage
        consistency_pct = round((matched / max(1, total)) * 100, 1)

        # Level
        if consistency_pct >= 99.9:
            level = "identical"
        elif consistency_pct >= 90:
            level = "minor"
        elif consistency_pct >= 70:
            level = "significant"
        elif consistency_pct >= 50:
            level = "major"
        else:
            level = "different"

        return DecisionConsistencyResult(
            decision_title_a=snap_a.decision_title,
            decision_title_b=snap_b.decision_title,
            observation_hash_a=snap_a.observation_hash,
            observation_hash_b=snap_b.observation_hash,
            same_decision=same_rec,
            same_score=same_score,
            score_delta=round(score_delta, 1),
            same_confidence=same_conf,
            confidence_delta=round(conf_delta, 4),
            same_explanation=same_evidence,
            same_alternatives=same_alts,
            same_execution_plan=same_actions,
            same_risk=same_risk,
            same_impact=same_impact,
            same_verification=same_verify,
            field_comparisons=comparisons,
            total_fields=total,
            matched_fields=matched,
            consistency_percentage=consistency_pct,
            level=level,
        )

    def compare_list(self, snapshots: List[DecisionSnapshot]) -> List[DecisionConsistencyResult]:
        """Bandingkan berpasangan dalam satu daftar."""
        results = []
        for i in range(len(snapshots)):
            for j in range(i + 1, len(snapshots)):
                results.append(self.compare(snapshots[i], snapshots[j]))
        return results

    def aggregate_report(self, results: List[DecisionConsistencyResult]) -> dict:
        """Laporan agregat dari daftar hasil perbandingan."""
        if not results:
            return {"total_comparisons": 0, "average_consistency": 0.0}

        total_consistency = sum(r.consistency_percentage for r in results)
        avg = round(total_consistency / len(results), 1)

        level_counts: Dict[str, int] = {}
        for r in results:
            level_counts[r.level] = level_counts.get(r.level, 0) + 1

        return {
            "total_comparisons": len(results),
            "average_consistency": avg,
            "level_distribution": level_counts,
            "min_consistency": round(min(r.consistency_percentage for r in results), 1),
            "max_consistency": round(max(r.consistency_percentage for r in results), 1),
        }
