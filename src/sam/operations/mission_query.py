"""
MissionQueryEngine — Natural querying of mission state.

Answers conversational questions about missions deterministically.
No LLM, no SQL. Designed for conversation integration.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MissionQueryResult:
    """Structured answer from a mission query."""
    query_type: str  # "running" | "failed" | "waiting_approval" | "by_workspace" | "highest_risk" | "completed_today"
    missions: list[dict] = field(default_factory=list)
    count: int = 0
    summary: str = ""


# ── Query patterns ────────────────────────────────────────────────────

_PATTERN_RUNNING = [
    "sedang berjalan", "running", "aktif", "berlangsung", "current",
]

_PATTERN_FAILED = [
    "gagal", "failed", "error", "bermasalah", "stuck", "stalled",
]

_PATTERN_WAITING_APPROVAL = [
    "menunggu approval", "waiting approval", "pending approval",
    "butuh persetujuan", "menunggu persetujuan",
]

_PATTERN_BY_WORKSPACE = [
    "workspace ini", "this workspace", "di workspace",
]

_PATTERN_HIGHEST_RISK = [
    "paling berisiko", "highest risk", "most risky", "critical",
    "berbahaya", "paling kritis",
]

_PATTERN_COMPLETED_TODAY = [
    "selesai hari ini", "completed today", "done today",
    "selesai", "berhasil hari ini",
]


class MissionQueryEngine:
    """Answers conversational mission queries using domain objects."""

    def __init__(self, mission_repo: Optional[object] = None,
                 timeline_store: Optional[object] = None) -> None:
        self._repo = mission_repo
        self._timeline = timeline_store

    # ── Query classification ──────────────────────────────────────────

    def classify(self, query: str) -> str:
        q = query.lower().strip()
        for pat in _PATTERN_RUNNING:
            if pat in q:
                return "running"
        for pat in _PATTERN_FAILED:
            if pat in q:
                return "failed"
        for pat in _PATTERN_WAITING_APPROVAL:
            if pat in q:
                return "waiting_approval"
        for pat in _PATTERN_BY_WORKSPACE:
            if pat in q:
                return "by_workspace"
        for pat in _PATTERN_HIGHEST_RISK:
            if pat in q:
                return "highest_risk"
        for pat in _PATTERN_COMPLETED_TODAY:
            if pat in q:
                return "completed_today"
        return "running"

    # ── Execute ───────────────────────────────────────────────────────

    def execute(self, query: str) -> MissionQueryResult:
        qtype = self.classify(query)

        if qtype == "running":
            missions = self._filter_missions(state="running") or []
        elif qtype == "failed":
            missions = self._filter_missions(state="failed") or []
        elif qtype == "waiting_approval":
            missions = self._filter_missions(state="waiting_approval") or []
        elif qtype == "by_workspace":
            missions = self._filter_by_workspace() or []
        elif qtype == "highest_risk":
            missions = self._filter_highest_risk() or []
        elif qtype == "completed_today":
            missions = self._filter_completed_today() or []
        else:
            missions = []

        result = MissionQueryResult(
            query_type=qtype,
            missions=missions,
            count=len(missions),
        )

        # Build summary
        if not missions:
            result.summary = self._empty_message(qtype)
        elif qtype == "running":
            result.summary = f"{len(missions)} mission(s) still running"
        elif qtype == "failed":
            result.summary = f"{len(missions)} failed mission(s)"
        elif qtype == "waiting_approval":
            result.summary = f"{len(missions)} mission(s) waiting for approval"
        elif qtype == "by_workspace":
            result.summary = f"{len(missions)} mission(s) in this workspace"
        elif qtype == "highest_risk":
            result.summary = f"{len(missions)} high/critical risk mission(s)"
        elif qtype == "completed_today":
            result.summary = f"{len(missions)} mission(s) completed today"

        return result

    # ── Internal filters ──────────────────────────────────────────────

    def _filter_missions(self, state: str) -> list[dict]:
        """Fetch missions by state from the repository."""
        repo = self._repo
        if not repo:
            return []

        try:
            if hasattr(repo, "list_by_state"):
                raw = repo.list_by_state(state)
            elif hasattr(repo, "get_all"):
                all_missions = repo.get_all()
                raw = [m for m in (all_missions or [])
                       if getattr(m, "state", None) == state]
            else:
                return []

            return [self._mission_to_dict(m) for m in (raw or [])]
        except Exception:
            return []

    def _filter_by_workspace(self) -> list[dict]:
        repo = self._repo
        if not repo:
            return []
        try:
            if hasattr(repo, "list_by_workspace"):
                raw = repo.list_by_workspace("/home/runner/work/SAM/SAM")
                return [self._mission_to_dict(m) for m in (raw or [])]
            return []
        except Exception:
            return []

    def _filter_highest_risk(self) -> list[dict]:
        repo = self._repo
        if not repo:
            return []
        try:
            if hasattr(repo, "get_all"):
                all_missions = repo.get_all()
                risky = [m for m in (all_missions or [])
                         if getattr(m, "risk_level", "low") in ("high", "critical")]
                return [self._mission_to_dict(m) for m in risky]
            return []
        except Exception:
            return []

    def _filter_completed_today(self) -> list[dict]:
        repo = self._repo
        if not repo:
            return []
        try:
            if hasattr(repo, "list_completed_today"):
                raw = repo.list_completed_today()
                return [self._mission_to_dict(m) for m in (raw or [])]
            elif hasattr(repo, "get_all"):
                all_missions = repo.get_all()
                today = [m for m in (all_missions or [])
                         if getattr(m, "state", None) == "completed"]
                return [self._mission_to_dict(m) for m in today]
            return []
        except Exception:
            return []

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _mission_to_dict(mission: object) -> dict:
        if isinstance(mission, dict):
            return mission
        d = {}
        for attr in ("mission_id", "id", "name", "state", "status",
                     "risk_level", "workspace", "created_at", "updated_at",
                     "priority", "checkpoint"):
            try:
                v = getattr(mission, attr, None)
                if v is not None:
                    d[attr] = v
            except Exception:
                pass
        return d

    @staticmethod
    def _empty_message(qtype: str) -> str:
        messages = {
            "running": "No missions currently running.",
            "failed": "No failed missions.",
            "waiting_approval": "No missions waiting for approval.",
            "by_workspace": "No missions in this workspace.",
            "highest_risk": "No high-risk missions.",
            "completed_today": "No missions completed today.",
        }
        return messages.get(qtype, "No matching missions found.")
