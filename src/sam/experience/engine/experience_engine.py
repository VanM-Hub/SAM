"""
Experience Engine — menerjemahkan data dari Operations Engine ke ViewModel.
"""

from typing import Optional, List
from datetime import datetime, timedelta

from ...operations.engine.context import ContextEngine
from ...operations.engine.status import StatusEngine
from ...operations.engine.task import TaskEngine
from ...operations.engine.knowledge import KnowledgeEngine
from ...operations.engine.history import HistoryEngine
from ...operations.engine.settings import SettingsEngine
from ...operations.engine.explain import ExplainabilityEngine
from ...operations.protection import ProtectionEngine
from ...telemetry.service import TelemetryService

from .models import (
    SystemHealth, SystemStatus, Purpose, CurrentActivity, ActivityItem,
    AttentionItem, RecommendationItem, HomeExperience,
    TimelineEntry, TimelineGroup, ActivityExperience,
    WorkItem, WorkStep, WorkProgress, WorkExperience,
    LearnedItem, KnowledgeExperience,
    HistoryStory, HistoryExperience,
    SettingsGroup, SettingsExperience,
    NotificationItem, NotificationExperience,
    AssistantAnswer, AssistantExperience,
)


class ExperienceEngine:
    """Layer ViewModel — UI hanya membaca dari sini."""

    def __init__(self, telemetry):
        self.telemetry = telemetry
        self.context_engine = ContextEngine()
        self.status_engine = StatusEngine(telemetry)
        self.task_engine = TaskEngine(telemetry)
        self.knowledge_engine = KnowledgeEngine(telemetry)
        self.history_engine = HistoryEngine(telemetry)
        self.settings_engine = SettingsEngine()
        self.explain_engine = ExplainabilityEngine(telemetry)
        self.protection = ProtectionEngine()

    # ======================================================================
    # HOME
    # ======================================================================

    def build_home(self) -> HomeExperience:
        """Apakah sistem sehat? Apa yang terjadi? Perlu tindakan?"""
        raw_status = self.status_engine.get_status()
        health_score = self.status_engine.get_health_score()

        # System health
        if raw_status.value == "healthy":
            status = SystemStatus.HEALTHY
            message = "SAM is Healthy"
            detail = "Everything is operating normally."
        elif raw_status.value == "degraded" or raw_status.value == "unhealthy":
            status = SystemStatus.PROBLEM
            message = "SAM needs attention"
            detail = self.status_engine.get_status_message()
        elif raw_status.value == "recovering":
            status = SystemStatus.RECOVERING
            message = "SAM is recovering"
            detail = self.status_engine.get_status_message()
        elif raw_status.value == "learning":
            status = SystemStatus.LEARNING
            message = "SAM is learning"
            detail = self.status_engine.get_status_message()
        else:
            status = SystemStatus.HEALTHY
            message = "SAM is Healthy"
            detail = "Everything is operating normally."

        # Protection cycle
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Schedule protection cycle
                task = asyncio.ensure_future(
                    self.protection.run_cycle(self.telemetry)
                )
                report = asyncio.get_event_loop().run_until_complete(task)
                prot_level = report.level.value
                prot_summary = report.summary
            else:
                prot_level = ""
                prot_summary = ""
        except Exception:
            prot_level = ""
            prot_summary = ""

        health = SystemHealth(
            status=status,
            message=message,
            detail=detail,
            health_score=health_score,
            protection_level=prot_level,
            protection_summary=prot_summary,
        )

        # Purpose
        ctx = self.context_engine.get_context()
        purpose = Purpose(name=ctx.mission_name, status="active")

        # Current activity
        recent = self.telemetry.get_recent(5)
        activities = []
        for e in recent:
            ts = e.timestamp.strftime("%H:%M")
            activities.append(ActivityItem(
                time=ts,
                description=e.message[:60] if e.message else e.type.value,
            ))

        last_activity = activities[0].description if activities else "Monitoring Runtime"
        current = CurrentActivity(
            title=last_activity,
            description="",
            activity_log=activities[:3],
        )

        # Attention
        pending_tasks = self.task_engine.get_pending_approvals()
        if pending_tasks:
            attention = AttentionItem(
                needs_attention=True,
                message="Approval required",
                action="Review",
                reason=pending_tasks[0].name,
            )
        elif raw_status.value in ("degraded", "unhealthy"):
            attention = AttentionItem(
                needs_attention=True,
                message=detail,
                action="Investigate",
            )
        else:
            attention = AttentionItem(
                needs_attention=False,
                message="No action required",
            )

        # Recommendations
        recs = self.knowledge_engine.get_recommendations()
        recommendations = []
        for r in recs[:3]:
            recommendations.append(RecommendationItem(
                message=r.title,
                confidence=r.confidence,
            ))
        if not recommendations:
            recommendations.append(RecommendationItem(message="Nothing recommended."))

        return HomeExperience(
            health=health,
            purpose=purpose,
            current_activity=current,
            attention=attention,
            recommendations=recommendations,
        )

    # ======================================================================
    # ACTIVITY / TIMELINE
    # ======================================================================

    def build_activity(self) -> ActivityExperience:
        """Timeline kronologis aktivitas manusia."""
        filters = self.history_engine.__class__.__module__
        from ...experience.models.history import HistoryFilter
        model = self.history_engine.get_history(HistoryFilter(limit=50))

        groups = []
        for day in model.days[:7]:
            now = datetime.utcnow()
            delta = now - day.date
            if delta.days == 0:
                label = "Today"
            elif delta.days == 1:
                label = "Yesterday"
            elif delta.days <= 7:
                label = "{} days ago".format(delta.days)
            else:
                label = day.date.strftime("%B %d")

            entries = []
            for e in day.entries[:10]:
                entries.append(TimelineEntry(
                    time=e.timestamp.strftime("%H:%M"),
                    description=e.title[:80],
                    details=e.description[:200] if e.description else None,
                ))
            if entries:
                groups.append(TimelineGroup(label=label, entries=entries))

        return ActivityExperience(groups=groups)

    # ======================================================================
    # WORK
    # ======================================================================

    def build_work(self) -> WorkExperience:
        """Pekerjaan aktif."""
        tasks = self.task_engine.get_tasks()

        items = []
        for t in tasks[:10]:
            total_steps = max(len(t.steps), 1)
            current = min(t.current_step_index + 1, total_steps)
            steps = []
            for i, s in enumerate(t.steps[:7]):
                steps.append(WorkStep(
                    name=s.name[:40],
                    active=(i == t.current_step_index),
                    completed=(s.status.value == "completed"),
                ))

            if not steps:
                steps.append(WorkStep(name=t.name[:40], active=(t.status.value == "running"), completed=(t.status.value == "completed")))

            work_status = t.status.value
            if t.needs_approval:
                work_status = "Review required"

            items.append(WorkItem(
                title=t.name[:50],
                status=work_status,
                progress=WorkProgress(
                    current_step=current,
                    total_steps=total_steps,
                    percent=int(t.progress),
                    estimated_remaining="{}% complete".format(int(t.progress)),
                ),
                steps=steps,
                approval_needed=t.needs_approval,
                approval_reason=t.description[:60] if t.description else None,
            ))

        return WorkExperience(items=items)

    # ======================================================================
    # KNOWLEDGE
    # ======================================================================

    def build_knowledge(self) -> KnowledgeExperience:
        """Things SAM Learned."""
        model = self.knowledge_engine.get_knowledge()

        items = []
        for entry in model.entries[:15]:
            ts = None
            if hasattr(entry, 'timestamp') and entry.timestamp:
                delta = datetime.utcnow() - entry.timestamp
                if delta.days == 0:
                    ts = "Today"
                elif delta.days == 1:
                    ts = "Yesterday"
                elif delta.days < 7:
                    ts = "{} days ago".format(delta.days)
                else:
                    ts = entry.timestamp.strftime("%b %d")

            severity = "info"
            if entry.type.value == "recommendation":
                severity = "recommendation"
            elif entry.type.value == "pattern":
                severity = "warning"

            items.append(LearnedItem(
                title=entry.title[:80],
                confidence=entry.confidence if entry.confidence > 0 else None,
                severity=severity,
                timestamp=ts,
            ))

        if not items:
            items.append(LearnedItem(
                title="No knowledge yet. SAM is still learning.",
                severity="info",
            ))

        return KnowledgeExperience(items=items)

    # ======================================================================
    # HISTORY
    # ======================================================================

    def build_history(self) -> HistoryExperience:
        """Riwayat operasional berbentuk narasi."""
        events = self.history_engine.get_timeline(limit=30)

        stories = []
        current_label = None
        current_events = []

        for e in events:
            now = datetime.utcnow()
            delta = now - e.timestamp
            if delta.days == 0:
                label = "Today"
            elif delta.days == 1:
                label = "Yesterday"
            elif delta.days < 7:
                label = "{} days ago".format(delta.days)
            else:
                label = e.timestamp.strftime("%B %d")

            if label != current_label:
                if current_label and current_events:
                    stories.append(HistoryStory(label=current_label, events=current_events))
                current_label = label
                current_events = []

            current_events.append(e.title[:80])

        if current_label and current_events:
            stories.append(HistoryStory(label=current_label, events=current_events))

        return HistoryExperience(stories=stories)

    # ======================================================================
    # SETTINGS
    # ======================================================================

    def build_settings(self) -> SettingsExperience:
        """Pengaturan dalam kelompok manusia."""
        model = self.settings_engine.get_settings()

        groups = []
        for section in model.sections:
            name_map = {
                "runtime": "Runtime",
                "mission": "Purpose",
                "autonomy": "Autonomy",
                "policy": "Safety",
                "plugin": "Plugins",
                "hosting": "Updates",
            }
            display_name = name_map.get(section.category.value, section.name)

            settings = {}
            for item in section.items:
                key = item.key.split(".")[-1].replace("_", " ").title()
                settings[key] = str(item.value)

            groups.append(SettingsGroup(
                name=display_name,
                settings=settings,
                editable=True,
            ))

        return SettingsExperience(groups=groups)

    # ======================================================================
    # NOTIFICATION
    # ======================================================================

    def build_notifications(self) -> NotificationExperience:
        """Inbox notifikasi."""
        items = []

        # Pending approvals
        for t in self.task_engine.get_pending_approvals()[:3]:
            items.append(NotificationItem(
                type="approval",
                message="Approval required: {}".format(t.name[:40]),
                timestamp=t.created_at.strftime("%H:%M") if t.created_at else "Now",
                action="Review",
            ))

        # Recent recommendations
        for r in self.knowledge_engine.get_recommendations()[:3]:
            items.append(NotificationItem(
                type="recommendation",
                message="New recommendation: {}".format(r.title[:40]),
                timestamp="Now",
            ))

        if not items:
            items.append(NotificationItem(
                type="info",
                message="No notifications",
                timestamp="",
            ))

        return NotificationExperience(items=items)

    # ======================================================================
    # ASSISTANT
    # ======================================================================

    def ask(self, question: str) -> AssistantAnswer:
        """Tanya Assistant (tanpa LLM, pakai Explanation Engine)."""
        question_lower = question.lower()

        if "terjadi" in question_lower or "happening" in question_lower or "what" in question_lower:
            # Apa yang terjadi?
            recent = self.explain_engine.explain_recent(limit=3)
            if recent:
                lines = []
                for e in recent:
                    lines.append("{} — {}".format(e.title, e.why[:60]))
                answer = "\n".join(lines[:3])
                details = "Lihat Activity untuk timeline lengkap."
            else:
                answer = "Nothing significant is happening."
            return AssistantAnswer(
                question=question,
                answer=answer,
                details=details if 'details' in dir() else None,
            )

        elif "sehat" in question_lower or "healthy" in question_lower or "status" in question_lower:
            # Apakah sistem sehat?
            health = self.status_engine.get_status()
            msg = self.status_engine.get_status_message()
            return AssistantAnswer(
                question=question,
                answer="SAM is {}: {}".format(health.value, msg),
            )

        elif "kenapa" in question_lower or "why" in question_lower:
            # Mengapa?
            recent_explain = self.explain_engine.explain_recent(limit=1)
            if recent_explain:
                e = recent_explain[0]
                return AssistantAnswer(
                    question=question,
                    answer=e.why[:200],
                    details="Impact: {}. Recommendation: {}".format(
                        e.impact.description if e.impact else "N/A",
                        e.recommendation.description if e.recommendation else "N/A",
                    ) if e.impact or e.recommendation else None,
                    action=e.recommendation.action if e.recommendation else None,
                )
            return AssistantAnswer(
                question=question,
                answer="There are no recent events that need explanation.",
            )

        elif "rekomendasi" in question_lower or "recommend" in question_lower or "saran" in question_lower:
            # Rekomendasi?
            recs = self.knowledge_engine.get_recommendations()
            if recs:
                lines = ["- " + r.title[:80] for r in recs[:3]]
                return AssistantAnswer(
                    question=question,
                    answer="Recommendations:\n" + "\n".join(lines),
                )
            return AssistantAnswer(
                question=question,
                answer="No recommendations at this time.",
            )

        elif "approv" in question_lower or "setuju" in question_lower or "izin" in question_lower:
            # Approval?
            pending = self.task_engine.get_pending_approvals()
            if pending:
                return AssistantAnswer(
                    question=question,
                    answer="{} work item(s) need approval.".format(len(pending)),
                    details=pending[0].name if pending else None,
                    action="Review",
                )
            return AssistantAnswer(
                question=question,
                answer="No pending approvals.",
            )

        else:
            return AssistantAnswer(
                question=question,
                answer="I'm not sure I understand. You can ask:\n"
                        "- What is happening?\n"
                        "- Is the system healthy?\n"
                        "- Why did this happen?\n"
                        "- What do you recommend?\n"
                        "- Are there any approvals?",
            )

    def build_assistant(self, questions: List[str]) -> AssistantExperience:
        """Halaman Assistant."""
        answers = [self.ask(q) for q in questions]
        return AssistantExperience(answers=answers)
