"""
OP-128 — Conversation Integration.

Conversation harus dapat menjawab pertanyaan tentang mission.
Semua jawaban berasal dari MissionController + MissionScheduler + LongRunningController.

Tidak ada renderer baru. Hanya API query.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from sam.operations.mission_controller import MissionController, MissionState
from sam.operations.mission_scheduler import MissionScheduler, SchedulerState
from sam.operations.mission_timeline import TimelineStore
from sam.operations.mission_long import LongRunningController, Checkpoint
from sam.operations.workspace_lock import WorkspaceLockManager


@dataclass
class ConversationMissionAnswer:
    """DTO untuk jawaban Conversation tentang mission.

    BUKAN renderer. Hanya data container.
    """
    success: bool
    answer: str
    data: Optional[dict] = None

    def to_text(self) -> str:
        return self.answer


class MissionConversationBridge:
    """Bridge antara Conversation dan sistem Mission.

    Method untuk pertanyaan umum:
      list_missions(filter) -> ConversationMissionAnswer
      get_mission_status(mission_id) -> ConversationMissionAnswer
      get_mission_timeline(mission_id) -> ConversationMissionAnswer
      get_scheduler_stats() -> ConversationMissionAnswer
      get_locks() -> ConversationMissionAnswer
    Method untuk aksi:
      cancel_mission(mission_id) -> ConversationMissionAnswer
      resume_mission(mission_id) -> ConversationMissionAnswer
    """

    def __init__(self,
                 mission_controller: Optional[MissionController] = None,
                 scheduler: Optional[MissionScheduler] = None,
                 timeline_store: Optional[TimelineStore] = None,
                 long_controller: Optional[LongRunningController] = None,
                 lock_manager: Optional[WorkspaceLockManager] = None):
        self.mc = mission_controller or MissionController()
        self.sched = scheduler or MissionScheduler()
        self.timeline = timeline_store or TimelineStore()
        self.long = long_controller or LongRunningController()
        self.locks = lock_manager or WorkspaceLockManager()

    # --- QUERY: WHAT MISSIONS ARE RUNNING? ---

    def list_running_missions(self) -> ConversationMissionAnswer:
        """What missions are running?"""
        running = self.sched.list_running()
        if not running:
            return ConversationMissionAnswer(True, "No missions running.")
        lines = ["Running missions:"]
        for m in running:
            lines.append("  {} ({})".format(m.mission_id, m.priority.label))
        return ConversationMissionAnswer(True, "\n".join(lines),
                                         data={"missions": [m.to_dict() for m in running]})

    def list_pending_missions(self) -> ConversationMissionAnswer:
        """What missions are waiting?"""
        pending = self.sched.list_scheduled()
        if not pending:
            return ConversationMissionAnswer(True, "No pending missions.")
        lines = ["Pending missions:"]
        for m in pending:
            lines.append("  {} ({}) — status: {}".format(
                m.mission_id, m.priority.label, m.status))
        return ConversationMissionAnswer(True, "\n".join(lines),
                                         data={"missions": [m.to_dict() for m in pending]})

    def list_completed_missions(self) -> ConversationMissionAnswer:
        """Show completed missions."""
        completed = self.sched.list_completed()
        if not completed:
            return ConversationMissionAnswer(True, "No completed missions.")
        lines = ["Completed missions:"]
        for m in completed:
            lines.append("  {} — {}".format(m.mission_id, m.status))
        return ConversationMissionAnswer(True, "\n".join(lines),
                                         data={"missions": [m.to_dict() for m in completed]})

    def list_all_missions(self, state_filter: Optional[str] = None) -> ConversationMissionAnswer:
        """List all missions."""
        if state_filter and state_filter.upper() in [s.value for s in MissionState]:
            f = MissionState(state_filter.upper())
            missions = self.mc.list_missions(f)
        else:
            missions = self.mc.list_missions()

        if not missions:
            return ConversationMissionAnswer(True, "No missions found.")
        lines = ["Missions:"]
        for m in missions:
            lines.append("  {} — {}".format(m.mission_id, m.state.value))
        return ConversationMissionAnswer(True, "\n".join(lines),
                                         data={"missions": [m.to_dict() for m in missions]})

    # --- QUERY: WHAT IS A SPECIFIC MISSION DOING? ---

    def get_mission_status(self, mission_id: str) -> ConversationMissionAnswer:
        """What is Mission #12 doing?"""
        m = self.mc.get_mission(mission_id)
        if m is None:
            s = self.sched.get_status(mission_id)
            if s:
                return ConversationMissionAnswer(True,
                    "Mission {} is in scheduler: {} ({}).".format(
                        mission_id, s['status'], s['priority']),
                    data={'mission': s, 'source': 'scheduler'})
            return ConversationMissionAnswer(False,
                "Mission {} not found.".format(mission_id))

        # Cek checkpoint
        ck = self.long.get_checkpoint(mission_id)
        ck_info = ""
        if ck:
            ck_info = " Checkpoint: step {}, state {}.".format(
                ck.step_index, ck.state)

        # Cek timeline
        tl = self.timeline.get_timeline(mission_id)
        last = tl.last_event if tl else None
        last_info = ""
        if last:
            last_info = " Last event: {} — {}.".format(
                last.event_type, last.description)

        txt = "Mission {}: {}.{} {}".format(
            mission_id, m.state.value, ck_info, last_info)
        return ConversationMissionAnswer(
            True, txt,
            data={
                'mission': m.to_dict(),
                'last_event': last.to_dict() if last else None,
            })

    def get_mission_timeline(self, mission_id: str) -> ConversationMissionAnswer:
        """Get timeline for a mission."""
        tl = self.timeline.get_timeline(mission_id)
        if tl is None or tl.count == 0:
            return ConversationMissionAnswer(False,
                "No timeline for {}.".format(mission_id))
        return ConversationMissionAnswer(
            True, tl.to_text(),
            data={'events': tl.to_dict(), 'count': tl.count})

    # --- QUERY: WHY IS A MISSION WAITING? ---

    def why_waiting(self, mission_id: str) -> ConversationMissionAnswer:
        """Why is Mission #5 waiting?"""
        s = self.sched.get_status(mission_id)
        if s is None:
            m = self.mc.get_mission(mission_id)
            if m is None:
                return ConversationMissionAnswer(False,
                    "Mission {} not found.".format(mission_id))
            if m.state == MissionState.WAITING_APPROVAL:
                return ConversationMissionAnswer(True,
                    "Mission {} is waiting for human approval.".format(mission_id))
            return ConversationMissionAnswer(True,
                "Mission {} is in state: {}.".format(mission_id, m.state.value))

        if s['status'] in ('pending', 'paused'):
            # Cek apakah ada resource conflict
            resources = s.get('resources', [])
            for res in resources:
                lock = self.locks.get_lock(res)
                if lock and lock.mission_id != mission_id:
                    return ConversationMissionAnswer(True,
                        "Mission {} is waiting for resource '{}' held by {}.".format(
                            mission_id, res, lock.mission_id))
        return ConversationMissionAnswer(True,
            "Mission {} is in scheduler: {}.".format(mission_id, s['status']))

    # --- QUERY: WHAT FAILED TODAY? ---

    def list_failed_today(self) -> ConversationMissionAnswer:
        """What failed today?"""
        today = datetime.now().isoformat()[:10]
        failed = []
        for m in self.sched.list_completed():
            if m.status == 'failed':
                failed.append(m)

        if not failed:
            return ConversationMissionAnswer(True, "No failed missions today.")

        lines = ["Failed missions:"]
        for m in failed:
            lines.append("  {} — {}: {}".format(
                m.mission_id, m.error[:50] if m.error else "unknown", m.priority.label))
        return ConversationMissionAnswer(True, "\n".join(lines),
                                         data={'failed': [m.to_dict() for m in failed]})

    # --- QUERY: SCHEDULER ---

    def get_scheduler_stats(self) -> ConversationMissionAnswer:
        """Get scheduler status."""
        stats = self.sched.get_stats()
        txt = "Scheduler: {}\n  Running: {}\n  Pending: {}\n  Completed: {}\n  Failed: {}\n  Locks: {}".format(
            stats['state'], stats['running'], stats['pending'],
            stats['completed'], stats['failed'], stats['active_locks'])
        return ConversationMissionAnswer(True, txt, data=stats)

    def get_locks(self) -> ConversationMissionAnswer:
        """Show active locks."""
        locks = self.locks.list_locks()
        if not locks:
            return ConversationMissionAnswer(True, "No active locks.")
        lines = ["Active locks:"]
        for lk in locks:
            lines.append("  {} held by {} ({:.0f}s elapsed)".format(
                lk.resource, lk.mission_id, lk.elapsed_seconds))
        return ConversationMissionAnswer(True, "\n".join(lines),
                                         data={'locks': [lk.to_dict() for lk in locks]})

    # --- ACTIONS ---

    def cancel_mission(self, mission_id: str, reason: str = "") -> ConversationMissionAnswer:
        """Cancel mission 8."""
        ok = self.sched.cancel(mission_id)
        if ok:
            # Mission mungkin tidak ada di controller (hanya di scheduler)
            m = self.mc.get_mission(mission_id)
            if m:
                self.mc.transition(mission_id, MissionState.CANCELLED, reason or "Cancelled via Conversation")
            self.timeline.add_event(mission_id, 'CANCELLED', reason or "Cancelled by operator")
            return ConversationMissionAnswer(True,
                "Mission {} cancelled.".format(mission_id))
        return ConversationMissionAnswer(False,
            "Could not cancel mission {}. Already completed or not found.".format(mission_id))

    def resume_mission(self, mission_id: str) -> ConversationMissionAnswer:
        """Resume mission."""
        ok = self.sched.resume(mission_id)
        if ok:
            self.mc.transition(mission_id, self.mc.get_state(mission_id),
                               "Resumed via Conversation")
            self.timeline.add_event(mission_id, 'RESUMED', "Mission resumed")
            return ConversationMissionAnswer(True,
                "Mission {} resumed.".format(mission_id))
        return ConversationMissionAnswer(False,
            "Could not resume mission {}. Not paused or not found.".format(mission_id))
