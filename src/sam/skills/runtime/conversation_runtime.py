"""Conversation Runtime Bridge — query read-only (Sprint 167)."""
from __future__ import annotations

from .skill_runtime import SkillRuntime
from .skill_summary import SkillSummarizer


class ConversationRuntimeBridge:
    """Bridge conversation — ringkasan skill runtime read-only."""

    def __init__(self, runtime: SkillRuntime) -> None:
        self._runtime = runtime

    def summary(self) -> dict:
        s = SkillSummarizer(self._runtime.registry).summary()
        return {"total": s.total_skills, "external_calls": s.external_calls}

    def run_status(self, skill_id: str) -> dict:
        res = self._runtime.run(skill_id)
        return {"ok": res.ok, "steps": res.steps, "external_calls": res.external_calls}
