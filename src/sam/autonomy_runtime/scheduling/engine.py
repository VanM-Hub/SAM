# Scheduling Engine - WP-14
# IP-3.2-002 (AO-3.2-001 / ED-3.2-002)
#
# Candidate execution schedule (PROPOSAL ONLY).
# Menghasilkan jadwal kandidat urutan kerja dari rencana runtime. Jadwal ini
# hanyalah USULAN deterministik - tidak menjadwalkan eksekusi nyata, tidak
# memicu aksi, tidak mengubah Runtime/Workflow/Governance.
#
# Prinsip: plan, never decide. Jadwal adalah proposal, bukan keputusan.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.planning.models import PlanStep, RuntimePlan


@dataclass(frozen=True)
class ScheduledStep:
    """Satu langkah berjadwal (kandidat). Immutable, proposal-only."""

    step_id: str
    sequence: int
    target: str
    action: str
    slot_label: str  # label jadwal (mis. "slot-1") - bukan waktu eksekusi nyata
    priority: int
    ready: bool  # apakah prasyaratnya terpenuhi saat ini (penilaian read-only)
    blockers: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "sequence": self.sequence,
            "target": self.target,
            "action": self.action,
            "slot_label": self.slot_label,
            "priority": self.priority,
            "ready": self.ready,
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class SchedulingProposal:
    """Jadwal kandidat lengkap. Proposal-only, immutable."""

    schedule_id: str
    plan_id: str
    steps: Tuple[ScheduledStep, ...] = ()
    ready_steps: Tuple[str, ...] = ()
    blocked_steps: Tuple[str, ...] = ()
    total_ready: int = 0
    total_blocked: int = 0
    status: str = "proposed"  # proposed | ready | blocked
    note: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "plan_id": self.plan_id,
            "steps": [s.as_dict() for s in self.steps],
            "ready_steps": list(self.ready_steps),
            "blocked_steps": list(self.blocked_steps),
            "total_ready": self.total_ready,
            "total_blocked": self.total_blocked,
            "status": self.status,
            "note": self.note,
        }


class SchedulingEngine:
    """Menyusun jadwal kandidat deterministik dari RuntimePlan (proposal)."""

    def __init__(self) -> None:
        pass

    def build_schedule(
        self,
        plan: RuntimePlan,
        available: Optional[Tuple[str, ...]] = None,
    ) -> SchedulingProposal:
        """Susun jadwal kandidat dari rencana.

        available = komponen yang saat ini tersedia (read-only penilaian).
        Urutan mengikuti urutan plan (sudah dependency-ordered oleh caller).
        """
        avail = set(available or ())
        scheduled: List[ScheduledStep] = []
        ready_ids: List[str] = []
        blocked_ids: List[str] = []

        # pasang urutan: urutkan steps by priority dulu (stabil), beri sequence
        ordered = sorted(plan.steps, key=lambda s: (-s.priority, s.step_id))
        for seq, step in enumerate(ordered, start=1):
            blockers: List[str] = []
            # prasyarat yang belum avail = blocker (evaluasi read-only)
            if step.prerequisite_ids:
                existing = set(avail)
                for dep in step.prerequisite_ids:
                    if dep not in existing:
                        blockers.append(dep)
            # siap bila semua prasyarat terpenuhi; readiness_gate hanyalah
            # deskripsi kondisi komponen target (bukan syarat kelayakan jadwal)
            ready = len(blockers) == 0
            slot = "slot-{}".format(seq)
            scheduled.append(ScheduledStep(
                step_id=step.step_id,
                sequence=seq,
                target=step.target,
                action=step.action,
                slot_label=slot,
                priority=step.priority,
                ready=ready,
                blockers=tuple(sorted(set(blockers))),
            ))
            if ready:
                ready_ids.append(step.step_id)
            else:
                blocked_ids.append(step.step_id)

        status = "ready" if ready_ids and not blocked_ids else (
            "blocked" if blocked_ids else "proposed"
        )
        note = _schedule_note(ready_ids, blocked_ids)
        return SchedulingProposal(
            schedule_id="schedule-{}-{}".format(plan.plan_id, _seed(plan)),
            plan_id=plan.plan_id,
            steps=tuple(scheduled),
            ready_steps=tuple(ready_ids),
            blocked_steps=tuple(blocked_ids),
            total_ready=len(ready_ids),
            total_blocked=len(blocked_ids),
            status=status,
            note=note,
        )


def _schedule_note(ready_ids: List[str], blocked_ids: List[str]) -> str:
    if not ready_ids and not blocked_ids:
        return "empty schedule (no steps to schedule)"
    if blocked_ids:
        return "{} ready, {} blocked; blocked steps require prerequisites".format(
            len(ready_ids), len(blocked_ids)
        )
    return "all {} steps ready (proposal only - not executed)".format(len(ready_ids))


def _seed(plan: RuntimePlan) -> str:
    import hashlib
    raw = "|".join([plan.plan_id, plan.state, ", ".join(plan.step_ids())])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:6]
