"""
OP-276 — Human Workload Balancer

Hitung beban kerja operasional:
  - pending approvals
  - pending missions
  - proposal count
  - review load

Output: WorkloadSnapshot (DTO — tidak melakukan assignment otomatis)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApproverLoad:
    approver_id: str
    pending_approvals: int = 0
    pending_reviews: int = 0
    total_pending: int = 0
    critical_pending: int = 0
    oldest_pending_hours: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "approver_id": self.approver_id,
            "pending_approvals": self.pending_approvals,
            "pending_reviews": self.pending_reviews,
            "total_pending": self.total_pending,
            "critical_pending": self.critical_pending,
            "oldest_pending_hours": self.oldest_pending_hours,
        }


@dataclass(frozen=True)
class WorkloadSnapshot:
    total_pending_approvals: int = 0
    total_pending_missions: int = 0
    total_proposals: int = 0
    total_review_load: int = 0
    approver_loads: tuple[ApproverLoad, ...] = ()
    avg_pending_per_approver: float = 0.0
    max_pending_per_approver: int = 0
    critical_approval_count: int = 0
    stalled_proposals: int = 0
    health_status: str = "healthy"  # healthy | moderate | overloaded

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_pending_approvals": self.total_pending_approvals,
            "total_pending_missions": self.total_pending_missions,
            "total_proposals": self.total_proposals,
            "total_review_load": self.total_review_load,
            "approver_loads": [a.to_dict() for a in self.approver_loads],
            "avg_pending_per_approver": self.avg_pending_per_approver,
            "max_pending_per_approver": self.max_pending_per_approver,
            "critical_approval_count": self.critical_approval_count,
            "stalled_proposals": self.stalled_proposals,
            "health_status": self.health_status,
        }


class WorkloadBalancer:
    """
    Menghitung beban kerja dari data operasional.

    Read-only — tidak melakukan assignment, tidak mengubah state.
    """

    # Threshold for overload detection
    STALLED_DAYS: float = 7.0
    OVERLOAD_THRESHOLD: int = 10

    def snapshot(self,
                 approvals: list[dict[str, Any]] | None = None,
                 missions: list[dict[str, Any]] | None = None,
                 proposals: list[dict[str, Any]] | None = None,
                 ) -> WorkloadSnapshot:
        """
        Generate workload snapshot.

        Args:
            approvals: list of approval dicts with keys: id, approver, status, severity, created_at
            missions: list of mission dicts with keys: id, status
            proposals: list of proposal dicts with keys: id, status, severity
        """
        apps = approvals or []
        miss = missions or []
        props = proposals or []

        # Per-approver load
        approver_map: dict[str, dict[str, Any]] = {}
        critical_count = 0

        for a in apps:
            approver = a.get("approver", "unknown")
            if approver not in approver_map:
                approver_map[approver] = {
                    "approvals": 0, "reviews": 0, "critical": 0,
                    "oldest_hours": 0.0,
                }
            approver_map[approver]["approvals"] += 1

            if str(a.get("severity", "")).lower() == "critical":
                approver_map[approver]["critical"] += 1
                critical_count += 1

            # Track oldest
            from datetime import datetime
            created = a.get("created_at")
            if created:
                try:
                    dt = datetime.fromisoformat(str(created))
                    hours = (datetime.now() - dt).total_seconds() / 3600
                    if hours > approver_map[approver]["oldest_hours"]:
                        approver_map[approver]["oldest_hours"] = hours
                except (ValueError, TypeError):
                    pass

        approver_loads: list[ApproverLoad] = []
        for approver_id, data in approver_map.items():
            total = data["approvals"] + data["reviews"]
            approver_loads.append(ApproverLoad(
                approver_id=approver_id,
                pending_approvals=data["approvals"],
                pending_reviews=data["reviews"],
                total_pending=total,
                critical_pending=data["critical"],
                oldest_pending_hours=round(data["oldest_hours"], 1),
            ))

        # Stalled proposals (pending > STALLED_DAYS)
        stalled = 0
        for p in props:
            if p.get("status") in ("pending", "draft", "waiting"):
                stalled += 1

        # Totals
        total_apps = len([a for a in apps if a.get("status") in ("pending", "waiting")])
        total_miss = len([m for m in miss if m.get("status") in ("pending", "running", "paused")])
        total_props = len(props)

        avg_load = round(total_apps / len(approver_loads), 1) if approver_loads else 0.0
        max_load = max((a.total_pending for a in approver_loads), default=0)

        health = "healthy"
        if max_load >= self.OVERLOAD_THRESHOLD * 2:
            health = "overloaded"
        elif max_load >= self.OVERLOAD_THRESHOLD:
            health = "moderate"

        return WorkloadSnapshot(
            total_pending_approvals=total_apps,
            total_pending_missions=total_miss,
            total_proposals=total_props,
            total_review_load=sum(a.pending_reviews for a in approver_loads),
            approver_loads=tuple(approver_loads),
            avg_pending_per_approver=avg_load,
            max_pending_per_approver=max_load,
            critical_approval_count=critical_count,
            stalled_proposals=stalled,
            health_status=health,
        )
