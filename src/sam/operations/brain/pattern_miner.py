"""
OP-261 — Pattern Discovery.

Temukan pola berulang dalam operational history.

Approach: rule-based, deterministic, no ML.
Pola terdeteksi dari sequence analysis sederhana.

Contoh pola yang dideteksi:
  - approval selalu lambat di jam tertentu
  - mission tertentu sering gagal
  - trust turun setiap N siklus
  - queue selalu penuh setelah spike finding
"""

from __future__ import annotations

import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class OperationalRecord:
    """A single operational record (finding, rec, proposal, etc.)."""
    record_id: str
    record_type: str  # "finding" | "recommendation" | "proposal" | "approval" | "execution" | "outcome"
    title: str
    timestamp: float = 0.0
    source: str = ""
    severity: str = "info"
    outcome: str = "unknown"  # "success" | "failure" | "pending" | "unknown"
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def hour_of_day(self) -> int:
        if self.timestamp <= 0:
            return -1
        return int(time.strftime("%H", time.localtime(self.timestamp)))

    @property
    def day_of_week(self) -> int:
        if self.timestamp <= 0:
            return -1
        return int(time.strftime("%w", time.localtime(self.timestamp)))


@dataclass
class DiscoveredPattern:
    """A detected operational pattern."""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    confidence: float  # 0.0 - 1.0
    severity: str = "info"
    example_records: List[str] = field(default_factory=list)
    first_seen: float = 0.0
    last_seen: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "confidence": round(self.confidence, 4),
            "severity": self.severity,
            "example_records": self.example_records[:5],
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


@dataclass
class PatternDiscoveryResult:
    """Complete pattern discovery result."""
    patterns: List[DiscoveredPattern] = field(default_factory=list)
    records_scanned: int = 0
    time_window_hours: float = 0.0
    generated_at: float = 0.0

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self.patterns]

    def get_severity_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for p in self.patterns:
            counts[p.severity] = counts.get(p.severity, 0) + 1
        return counts


# ── Engine ─────────────────────────────────────────────────────────


class PatternMiner:
    """
    Mendeteksi pola berulang dari operational records.

    Pola dideteksi dengan:
      1. Frekuensi per source per severity (mission A sering gagal)
      2. Temporal clusters (approval lambat di jam tertentu)
      3. Co-occurrence (finding X selalu diikuti finding Y)
      4. Outcome sequences (proposal → execution → failure loop)
    """

    def __init__(self):
        self._last_result: Optional[PatternDiscoveryResult] = None

    @property
    def last_result(self) -> Optional[PatternDiscoveryResult]:
        return self._last_result

    def discover(
        self,
        records: List[OperationalRecord],
        time_window_hours: float = 24.0,
    ) -> PatternDiscoveryResult:
        """Analyze records and discover patterns."""
        patterns: List[DiscoveredPattern] = []
        now = time.time()
        window_start = now - (time_window_hours * 3600)

        # Filter to recent
        recent = [r for r in records if r.timestamp >= window_start or r.timestamp <= 0]

        # 1. Source failure patterns
        patterns.extend(self._find_source_failure_patterns(recent))

        # 2. Temporal patterns (hour-of-day)
        patterns.extend(self._find_temporal_patterns(recent))

        # 3. Co-occurrence patterns
        patterns.extend(self._find_co_occurrence_patterns(recent))

        # 4. Outcome sequence patterns
        patterns.extend(self._find_outcome_sequences(recent))

        # 5. Severity patterns
        patterns.extend(self._find_severity_patterns(recent))

        result = PatternDiscoveryResult(
            patterns=patterns,
            records_scanned=len(recent),
            time_window_hours=time_window_hours,
            generated_at=now,
        )
        self._last_result = result
        return result

    # ── Detection methods ──────────────────────────────────────────

    def _find_source_failure_patterns(
        self, records: List[OperationalRecord]
    ) -> List[DiscoveredPattern]:
        """Find sources with high failure rates."""
        patterns: List[DiscoveredPattern] = []
        source_failures: Dict[str, int] = Counter()
        source_total: Dict[str, int] = Counter()

        for r in records:
            if r.outcome == "failure":
                source_failures[r.source] += 1
            source_total[r.source] += 1

        for source, total in source_total.items():
            if total < 3:
                continue
            fail_count = source_failures.get(source, 0)
            fail_rate = fail_count / total
            if fail_rate >= 0.5:
                patterns.append(DiscoveredPattern(
                    pattern_id=f"source_fail_{source}",
                    pattern_type="source_failure",
                    description=f"Source '{source}' has {fail_rate:.0%} failure rate ({fail_count}/{total})",
                    frequency=fail_count,
                    confidence=min(1.0, fail_rate * 1.2),
                    severity="critical" if fail_rate >= 0.8 else "warning",
                ))

        return patterns

    def _find_temporal_patterns(
        self, records: List[OperationalRecord]
    ) -> List[DiscoveredPattern]:
        """Find time-based patterns by hour."""
        patterns: List[DiscoveredPattern] = []
        hour_records: Dict[int, List[OperationalRecord]] = defaultdict(list)

        for r in records:
            h = r.hour_of_day
            if h >= 0:
                hour_records[h].append(r)

        for hour, recs in hour_records.items():
            if len(recs) < 3:
                continue
            failures = [r for r in recs if r.outcome == "failure"]
            slow_approvals = [
                r for r in recs
                if r.record_type == "approval" and r.duration_seconds > 300
            ]
            if len(failures) >= len(recs) * 0.5:
                patterns.append(DiscoveredPattern(
                    pattern_id=f"hour_fail_{hour:02d}",
                    pattern_type="temporal",
                    description=f"High failure rate at hour {hour:02d}:00 "
                                f"({len(failures)}/{len(recs)} records)",
                    frequency=len(failures),
                    confidence=0.7,
                    severity="warning",
                ))
            if len(slow_approvals) >= 3:
                patterns.append(DiscoveredPattern(
                    pattern_id=f"hour_slow_approval_{hour:02d}",
                    pattern_type="temporal",
                    description=f"Approval slowdown detected at hour {hour:02d}:00 "
                                f"({len(slow_approvals)} slow approvals)",
                    frequency=len(slow_approvals),
                    confidence=0.65,
                    severity="warning",
                ))

        return patterns

    def _find_co_occurrence_patterns(
        self, records: List[OperationalRecord]
    ) -> List[DiscoveredPattern]:
        """Find patterns of two record types co-occurring."""
        patterns: List[DiscoveredPattern] = []
        pairs: Dict[Tuple[str, str], List[OperationalRecord]] = defaultdict(list)

        # Sort by timestamp and look for near pairs
        sorted_recs = sorted(records, key=lambda r: r.timestamp)
        for i in range(len(sorted_recs) - 1):
            a = sorted_recs[i]
            b = sorted_recs[i + 1]
            if abs(a.timestamp - b.timestamp) < 600:  # within 10 min
                key = (a.record_type, b.record_type)
                if a.record_type != b.record_type:
                    pairs[key].append(a)
                    pairs[key].append(b)

        for (type_a, type_b), recs in pairs.items():
            if len(recs) < 4:
                continue
            patterns.append(DiscoveredPattern(
                pattern_id=f"cooccur_{type_a}_{type_b}",
                pattern_type="co_occurrence",
                description=f"'{type_a}' frequently followed by '{type_b}' "
                            f"within 10 minutes ({len(recs)//2} co-occurrences)",
                frequency=len(recs) // 2,
                confidence=0.6,
                severity="info",
            ))

        return patterns

    def _find_outcome_sequences(
        self, records: List[OperationalRecord]
    ) -> List[DiscoveredPattern]:
        """Find repeating outcome sequences (failure loops)."""
        patterns: List[DiscoveredPattern] = []
        failure_chains: Dict[str, int] = Counter()

        sorted_recs = sorted(records, key=lambda r: r.timestamp)
        chain: List[OperationalRecord] = []
        for r in sorted_recs:
            if r.outcome == "failure":
                chain.append(r)
            else:
                if len(chain) >= 3:
                    key = f"{chain[0].source}_chain_{len(chain)}"
                    failure_chains[key] += 1
                chain = []

        for chain_key, count in failure_chains.items():
            if count >= 2:
                source = chain_key.split("_chain_")[0]
                patterns.append(DiscoveredPattern(
                    pattern_id=chain_key,
                    pattern_type="failure_chain",
                    description=f"Repeated failure chain from '{source}' "
                                f"({count} occurrences of sequences of 3+ failures)",
                    frequency=count,
                    confidence=0.75,
                    severity="critical",
                ))

        return patterns

    def _find_severity_patterns(
        self, records: List[OperationalRecord]
    ) -> List[DiscoveredPattern]:
        """Find patterns in severity distribution."""
        patterns: List[DiscoveredPattern] = []
        critical_count = sum(1 for r in records if r.severity == "critical")
        total = len(records) if records else 1
        critical_rate = critical_count / total

        if critical_rate > 0.3 and critical_count >= 5:
            patterns.append(DiscoveredPattern(
                pattern_id="high_critical_rate",
                pattern_type="severity",
                description=f"High critical severity rate: {critical_rate:.0%} "
                            f"({critical_count}/{total} records)",
                frequency=critical_count,
                confidence=min(1.0, critical_rate * 1.1),
                severity="critical",
            ))

        return patterns


# ── Convenience ────────────────────────────────────────────────────


def discover_patterns(
    records: List[OperationalRecord],
    time_window_hours: float = 24.0,
) -> PatternDiscoveryResult:
    """One-shot: discover patterns from records."""
    miner = PatternMiner()
    return miner.discover(records, time_window_hours)


def build_record(
    record_id: str,
    record_type: str,
    title: str,
    source: str = "",
    outcome: str = "unknown",
    severity: str = "info",
    duration_seconds: float = 0.0,
    timestamp: Optional[float] = None,
) -> OperationalRecord:
    """Build a single operational record."""
    return OperationalRecord(
        record_id=record_id,
        record_type=record_type,
        title=title,
        timestamp=timestamp or time.time(),
        source=source,
        severity=severity,
        outcome=outcome,
        duration_seconds=duration_seconds,
    )
