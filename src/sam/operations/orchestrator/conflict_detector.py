"""
OP-272 — Conflict Detector

Deteksi konflik dalam proposal operasional:

  - resource conflict
  - approval conflict
  - duplicate proposal
  - overlapping mission
  - lock conflict
  - priority inversion
  - scheduling collision

Output: ConflictReport
Tidak melakukan resolve.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConflictKind(Enum):
    RESOURCE_CONFLICT = "resource_conflict"
    APPROVAL_CONFLICT = "approval_conflict"
    DUPLICATE_PROPOSAL = "duplicate_proposal"
    OVERLAPPING_MISSION = "overlapping_mission"
    LOCK_CONFLICT = "lock_conflict"
    PRIORITY_INVERSION = "priority_inversion"
    SCHEDULING_COLLISION = "scheduling_collision"


@dataclass(frozen=True)
class Conflict:
    kind: ConflictKind
    description: str
    involved_ids: tuple[str, ...]
    severity: str = "medium"  # low | medium | high | critical
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "description": self.description,
            "involved_ids": list(self.involved_ids),
            "severity": self.severity,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ConflictReport:
    conflicts: tuple[Conflict, ...] = ()
    total: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    critical_count: int = 0

    @property
    def has_conflicts(self) -> bool:
        return self.total > 0

    def by_kind(self, kind: ConflictKind) -> list[Conflict]:
        return [c for c in self.conflicts if c.kind == kind]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "conflicts": [c.to_dict() for c in self.conflicts],
        }


class ConflictDetector:
    """
    Deteksi konflik antar proposal/proyek.

    Membaca data dari proposal list dan domain snapshots,
    menghasilkan ConflictReport tanpa melakukan resolve.
    """

    def detect(self,
               proposals: list[dict[str, Any]],
               missions: list[dict[str, Any]] | None = None,
               locks: list[dict[str, Any]] | None = None,
               approvals: list[dict[str, Any]] | None = None,
               schedules: list[dict[str, Any]] | None = None,
               ) -> ConflictReport:
        """
        Run all conflict checks.
        """
        all_conflicts: list[Conflict] = []

        all_conflicts.extend(self._check_resource_conflict(proposals))
        all_conflicts.extend(self._check_approval_conflict(proposals, approvals))
        all_conflicts.extend(self._check_duplicate_proposal(proposals))
        all_conflicts.extend(self._check_overlapping_mission(proposals, missions))
        all_conflicts.extend(self._check_lock_conflict(proposals, locks))
        all_conflicts.extend(self._check_priority_inversion(proposals))
        all_conflicts.extend(self._check_scheduling_collision(proposals, schedules))

        return self._build_report(all_conflicts)

    # ── Internal Checkers ────────────────────────────────────────────

    def _check_resource_conflict(self, proposals: list[dict[str, Any]]) -> list[Conflict]:
        conflicts: list[Conflict] = []
        resource_map: dict[str, list[str]] = {}

        for p in proposals:
            for r in p.get("requires", []):
                resource_map.setdefault(r, []).append(p["id"])

        for resource, pids in resource_map.items():
            if len(pids) > 1:
                conflicts.append(Conflict(
                    kind=ConflictKind.RESOURCE_CONFLICT,
                    description=f"Resource '{resource}' dibutuhkan oleh {len(pids)} proposal",
                    involved_ids=tuple(pids),
                    severity="high" if len(pids) > 3 else "medium",
                    detail=f"Resource: {resource}",
                ))

        return conflicts

    def _check_approval_conflict(self, proposals: list[dict[str, Any]],
                                 approvals: list[dict[str, Any]] | None) -> list[Conflict]:
        if not approvals:
            return []
        conflicts: list[Conflict] = []
        # Jika 2 proposal membutuhkan approval dari user yang sama
        approver_map: dict[str, list[str]] = {}
        for a in approvals:
            approver = a.get("approver", "unknown")
            approver_map.setdefault(approver, []).append(a.get("proposal_id", a.get("id", "?")))

        for approver, pids in approver_map.items():
            if len(pids) > 5:
                conflicts.append(Conflict(
                    kind=ConflictKind.APPROVAL_CONFLICT,
                    description=f"Approver '{approver}' memiliki {len(pids)} pending approvals",
                    involved_ids=tuple(pids),
                    severity="medium",
                    detail=f"Approver: {approver}, count: {len(pids)}",
                ))

        return conflicts

    def _check_duplicate_proposal(self, proposals: list[dict[str, Any]]) -> list[Conflict]:
        conflicts: list[Conflict] = []
        seen: dict[str, list[str]] = {}

        for p in proposals:
            title = p.get("title", p.get("id", "")).strip().lower()
            seen.setdefault(title, []).append(p["id"])

        for title, pids in seen.items():
            if len(pids) > 1:
                conflicts.append(Conflict(
                    kind=ConflictKind.DUPLICATE_PROPOSAL,
                    description=f"Duplicate proposal: '{title}' muncul {len(pids)} kali",
                    involved_ids=tuple(pids),
                    severity="high",
                    detail=f"Title: {title}",
                ))

        return conflicts

    def _check_overlapping_mission(self, proposals: list[dict[str, Any]],
                                   missions: list[dict[str, Any]] | None) -> list[Conflict]:
        if not missions:
            return []
        conflicts: list[Conflict] = []
        # Deteksi mission dengan resource yang overlap
        mission_resources: dict[str, set[str]] = {}
        for m in missions:
            mids = set()
            for k in ("required_resources", "resources", "depends_on"):
                for item in m.get(k, []):
                    if isinstance(item, str):
                        mids.add(item)
            mission_resources[m["id"]] = mids

        for p in proposals:
            p_rids = set(p.get("requires", []))
            if not p_rids:
                continue
            for mid, m_rids in mission_resources.items():
                overlap = p_rids & m_rids
                if overlap:
                    conflicts.append(Conflict(
                        kind=ConflictKind.OVERLAPPING_MISSION,
                        description=f"Proposal {p['id']} overlap resource dengan mission {mid}",
                        involved_ids=(p["id"], mid),
                        severity="medium",
                        detail=f"Overlapping resources: {list(overlap)}",
                    ))

        return conflicts

    def _check_lock_conflict(self, proposals: list[dict[str, Any]],
                             locks: list[dict[str, Any]] | None) -> list[Conflict]:
        if not locks:
            return []
        conflicts: list[Conflict] = []
        locked_resources: set[str] = set()
        for lk in locks:
            for k in ("resource", "resource_id", "target"):
                v = lk.get(k)
                if v:
                    locked_resources.add(str(v))

        if not locked_resources:
            return conflicts

        for p in proposals:
            for r in p.get("requires", []):
                if r in locked_resources:
                    conflicts.append(Conflict(
                        kind=ConflictKind.LOCK_CONFLICT,
                        description=f"Resource '{r}' sedang di-lock oleh mission lain",
                        involved_ids=(p["id"],),
                        severity="high",
                        detail=f"Locked resource: {r}",
                    ))

        return conflicts

    def _check_priority_inversion(self, proposals: list[dict[str, Any]]) -> list[Conflict]:
        conflicts: list[Conflict] = []
        # Priority inversion: proposal priority tinggi tergantung pada low priority
        for p in proposals:
            p_priority = p.get("priority", 50)
            for dep_id in p.get("depends_on", []):
                dep = next((x for x in proposals if x["id"] == dep_id), None)
                if dep and dep.get("priority", 50) < p_priority:
                    conflicts.append(Conflict(
                        kind=ConflictKind.PRIORITY_INVERSION,
                        description=f"Priority inversion: {p['id']} (priority {p_priority}) "
                                    f"tergantung pada {dep_id} (priority {dep.get('priority', 50)})",
                        involved_ids=(p["id"], dep_id),
                        severity="medium",
                        detail=f"Higher priority depends on lower: {p_priority} > {dep.get('priority', 50)}",
                    ))

        return conflicts

    def _check_scheduling_collision(self, proposals: list[dict[str, Any]],
                                    schedules: list[dict[str, Any]] | None) -> list[Conflict]:
        if not schedules:
            return []
        conflicts: list[Conflict] = []
        # Deteksi jadwal yang bentrok
        time_slots: dict[str, list[str]] = {}
        for s in schedules:
            slot = s.get("time_slot", s.get("window", "unknown"))
            time_slots.setdefault(slot, []).append(s.get("id", "?"))

        for slot, sids in time_slots.items():
            if len(sids) > 1:
                for pid_candidate in [p["id"] for p in proposals]:
                    if pid_candidate in sids:
                        conflicts.append(Conflict(
                            kind=ConflictKind.SCHEDULING_COLLISION,
                            description=f"Scheduling collision di slot '{slot}': {len(sids)} item",
                            involved_ids=tuple(sids),
                            severity="medium",
                            detail=f"Time slot: {slot}",
                        ))
                        break

        return conflicts

    # ── Report Builder ───────────────────────────────────────────────

    def _build_report(self, conflicts: list[Conflict]) -> ConflictReport:
        return ConflictReport(
            conflicts=tuple(conflicts),
            total=len(conflicts),
            critical_count=sum(1 for c in conflicts if c.severity == "critical"),
            high_count=sum(1 for c in conflicts if c.severity == "high"),
            medium_count=sum(1 for c in conflicts if c.severity == "medium"),
            low_count=sum(1 for c in conflicts if c.severity == "low"),
        )
