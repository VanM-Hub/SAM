"""
OP-113 — Historical Decision Replay.

Replay engine — ambil snapshot observasi lama, replay seluruh keputusan,
bandingkan dengan keputusan historis.

Semua deterministik — tanpa LLM.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from datetime import datetime


@dataclass
class ReplayResult:
    """Hasil replay satu keputusan."""
    replay_id: str                      # "replay-001"
    decision_title: str
    observation_snapshot_id: str

    # Original (historical) decision
    historical_recommendation: str
    historical_score: float
    historical_confidence: float
    historical_risk: str
    historical_alternatives: List[str]
    historical_evidence: List[str]
    historical_policy_version: str

    # Replayed decision
    replayed_recommendation: str
    replayed_score: float
    replayed_confidence: float
    replayed_risk: str
    replayed_alternatives: List[str]
    replayed_evidence: List[str]
    replayed_policy_version: str = ""

    # Comparison
    matched: bool = False           # Rekomendasi cocok?
    changed: bool = False           # Ada perubahan?
    changed_fields: List[str] = field(default_factory=list)
    why_changed: str = ""           # Penjelasan determistik
    policy_version: str = ""        # Policy version saat replay
    evidence_difference: str = ""   # Evidence yang berbeda
    score_delta: float = 0.0

    # Flags
    version_mismatch: bool = False
    evidence_mismatch: bool = False

    def to_dict(self) -> dict:
        return {
            "replay_id": self.replay_id,
            "decision_title": self.decision_title,
            "matched": self.matched,
            "changed": self.changed,
            "changed_fields": self.changed_fields,
            "why_changed": self.why_changed[:80],
            "score_delta": self.score_delta,
            "version_mismatch": self.version_mismatch,
            "evidence_mismatch": self.evidence_mismatch,
        }


@dataclass
class ReplayPackage:
    """Kumpulan hasil replay."""
    results: List[ReplayResult] = field(default_factory=list)
    total: int = 0
    matched: int = 0
    changed: int = 0
    match_percentage: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "matched": self.matched,
            "changed": self.changed,
            "match_percentage": self.match_percentage,
        }

    def to_text(self) -> str:
        return "Replay: {total} decisions, {matched} matched ({pct}%), {changed} changed".format(
            total=self.total, matched=self.matched,
            pct=round(self.match_percentage, 1), changed=self.changed,
        )


@dataclass
class ReplayDecision:
    """Representasi satu keputusan untuk replay."""
    decision_title: str
    recommendation: str
    score: float
    confidence: float
    risk: str
    alternatives: List[str]
    evidence: List[str]
    policy_version: str = ""


class ReplayEngine:
    """Engine untuk replay keputusan.

    Cara pakai:
      engine = ReplayEngine()
      engine.register(policy_version, evidence, decision_fn)
      result = engine.replay('snapshot-001', historical, same_evidence)
    """

    def __init__(self):
        self._policy_version = "v4.3.0"
        self._replay_count = 0

    def replay(self, observation_snapshot_id: str,
               historical: ReplayDecision,
               replayed: ReplayDecision) -> ReplayResult:
        """Replay dan bandingkan.

        Args:
            observation_snapshot_id: ID snapshot observasi
            historical: Keputusan historis (dari log/audit)
            replayed: Keputusan hasil replay

        Returns:
            ReplayResult
        """
        self._replay_count += 1
        replay_id = "replay-{:04d}".format(self._replay_count)

        changed_fields: List[str] = []
        why_parts: List[str] = []

        # 1. Bandingkan recommendation
        rec_a = historical.recommendation.strip().lower()
        rec_b = replayed.recommendation.strip().lower()
        matched = rec_a == rec_b
        changed = not matched

        if not matched:
            changed_fields.append("recommendation")
            why_parts.append("recommendation: '{h}' → '{r}'".format(
                h=historical.recommendation, r=replayed.recommendation))

        # 2. Score
        score_delta = abs(historical.score - replayed.score)
        if historical.score != replayed.score:
            changed_fields.append("score")
            if not changed:
                changed = True

        # 3. Confidence
        if abs(historical.confidence - replayed.confidence) > 0.01:
            changed_fields.append("confidence")
            if not changed:
                changed = True

        # 4. Risk
        if historical.risk != replayed.risk:
            changed_fields.append("risk")
            why_parts.append("risk: {h} → {r}".format(h=historical.risk, r=replayed.risk))
            if not changed:
                changed = True

        # 5. Alternatives
        alt_set_a = set(a.lower().strip() for a in historical.alternatives)
        alt_set_b = set(a.lower().strip() for a in replayed.alternatives)
        if alt_set_a != alt_set_b:
            changed_fields.append("alternatives")
            why_parts.append("alternatives: {} vs {}".format(len(alt_set_a), len(alt_set_b)))
            if not changed:
                changed = True

        # 6. Evidence
        ev_set_a = set(e.lower().strip() for e in historical.evidence)
        ev_set_b = set(e.lower().strip() for e in replayed.evidence)
        evidence_mismatch = ev_set_a != ev_set_b

        # 7. Policy version
        version_mismatch = historical.policy_version != replayed.policy_version

        # Build why_changed
        if why_parts:
            why_changed = "; ".join(why_parts)
        elif version_mismatch:
            why_changed = "Policy version changed: {h} → {r}".format(
                h=historical.policy_version, r=replayed.policy_version)
        elif evidence_mismatch:
            why_changed = "Evidence changed: different set"
        elif score_delta > 5:
            why_changed = "Score changed by {:.1f}".format(score_delta)
        else:
            why_changed = ""

        # Evidence difference
        if evidence_mismatch:
            only_a = ev_set_a - ev_set_b
            only_b = ev_set_b - ev_set_a
            parts = []
            if only_a:
                parts.append("removed: {}".format(", ".join(list(only_a)[:3])))
            if only_b:
                parts.append("added: {}".format(", ".join(list(only_b)[:3])))
            evidence_diff = "; ".join(parts)
        else:
            evidence_diff = ""

        return ReplayResult(
            replay_id=replay_id,
            decision_title=historical.decision_title,
            observation_snapshot_id=observation_snapshot_id,
            historical_recommendation=historical.recommendation,
            historical_score=historical.score,
            historical_confidence=historical.confidence,
            historical_risk=historical.risk,
            historical_alternatives=historical.alternatives,
            historical_evidence=historical.evidence,
            historical_policy_version=historical.policy_version,
            replayed_recommendation=replayed.recommendation,
            replayed_score=replayed.score,
            replayed_confidence=replayed.confidence,
            replayed_risk=replayed.risk,
            replayed_alternatives=replayed.alternatives,
            replayed_evidence=replayed.evidence,
            replayed_policy_version=replayed.policy_version,
            matched=matched,
            changed=changed,
            changed_fields=changed_fields,
            why_changed=why_changed,
            policy_version=replayed.policy_version,
            evidence_difference=evidence_diff,
            score_delta=round(score_delta, 1),
            version_mismatch=version_mismatch,
            evidence_mismatch=evidence_mismatch,
        )

    def replay_batch(self, pairs: List[tuple]) -> ReplayPackage:
        """Replay batch.

        Args:
            pairs: List of (observation_snapshot_id, historical, replayed)

        Returns:
            ReplayPackage
        """
        results = []
        for obs_id, historical, replayed in pairs:
            results.append(self.replay(obs_id, historical, replayed))

        total = len(results)
        matched = sum(1 for r in results if r.matched)
        changed = sum(1 for r in results if r.changed and not r.matched)

        return ReplayPackage(
            results=results,
            total=total,
            matched=matched,
            changed=changed,
            match_percentage=round((matched / max(1, total)) * 100, 1),
        )


class HistoricalStore:
    """Penyimpanan historis in-memory untuk replay.

    Method:
      store(decision) -> str snapshot_id
      get(snapshot_id) -> ReplayDecision
      all() -> list of (snapshot_id, ReplayDecision)
    """

    def __init__(self):
        self._store: Dict[str, ReplayDecision] = {}
        self._counter = 0

    def store(self, decision: ReplayDecision) -> str:
        self._counter += 1
        sid = "snap-{:04d}".format(self._counter)
        self._store[sid] = decision
        return sid

    def get(self, snapshot_id: str) -> Optional[ReplayDecision]:
        return self._store.get(snapshot_id)

    def all(self) -> List[tuple]:
        return list(self._store.items())
