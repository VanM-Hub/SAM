"""
@internal
Experience Engine — COMPATIBILITY LAYER.

JANGAN gunakan untuk fitur baru.
Gunakan sam.observe() -> Conversation API.

Existing: TelemetryService -> ExperienceEngine
New: SAM() -> Conversation -> answer()/timeline()/etc

Stability: COMPAT (akan dihapus di v5)
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
from ...operations.situation import SituationAnalyzer, SituationReport, Situation
from ...operations.attention import AttentionAnalyzer, AttentionItem, AttentionScore
from ...operations.story import StoryService, Story, StoryType
from ...operations.presentation import PresentationRenderer, Presentation, Decision
from ...operations.recommendation import RecommendationPolicy, Recommendation
from ...operations.prediction import PredictionPolicy, Prediction
from ...operations.question_engine import QuestionEngine, HumanAnswer
from ...narrative import NarrativeBuilder, DailyBriefing, SituationBrief
from ...openclaw.connection import OpenClawAdapter
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
        self.openclaw = OpenClawAdapter()
        self.openclaw.bind_telemetry(telemetry)
        self.narrative = NarrativeBuilder()
        self.situation = SituationAnalyzer(self)
        self.attention = AttentionAnalyzer(self)
        self.story_builder = StoryService()
        self.presentation = PresentationRenderer()
        self.recommendation_engine = RecommendationPolicy(self)
        self.prediction_engine = PredictionPolicy(self)
        self.question_engine = QuestionEngine(self)

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
            message = "The system is healthy"
            detail = "Everything is operating normally."
        elif raw_status.value == "degraded" or raw_status.value == "unhealthy":
            status = SystemStatus.PROBLEM
            message = "The system needs attention"
            detail = self.status_engine.get_status_message()
        elif raw_status.value == "recovering":
            status = SystemStatus.RECOVERING
            message = "The system is recovering"
            detail = self.status_engine.get_status_message()
        elif raw_status.value == "learning":
            status = SystemStatus.LEARNING
            message = "The system is learning"
            detail = self.status_engine.get_status_message()
        else:
            status = SystemStatus.HEALTHY
            message = "The system is healthy"
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
    # OPENCLAW
    # ======================================================================

    def build_openclaw_status(self) -> dict:
        """Status koneksi OpenClaw."""
        status = self.openclaw.get_connection_status()
        return {
            "connected": status.connected,
            "last_sync": status.last_sync,
            "error": status.error,
            "status_sent": status.status_sent,
            "commands_processed": status.commands_processed,
        }

    async def sync_openclaw(self):
        """Kirim status SAM ke OpenClaw."""
        await self.openclaw.cycle(self)

    # ======================================================================
    # NARRATIVE ENGINE
    # ======================================================================

    def build_narrative_home(self) -> 'NarrativeBundle':
        """Dapatkan narrative untuk Home page."""
        home = self.build_home()
        return self.narrative.build_from_home(home)

    def build_narrative_activity(self) -> list:
        """Dapatkan narrative untuk Activity page."""
        activity = self.build_activity()
        return self.narrative.build_from_activity(activity)

    def build_narrative_work(self) -> list:
        """Dapatkan narrative untuk Work page."""
        work = self.build_work()
        return self.narrative.build_from_work(work)

    def build_narrative_knowledge(self) -> list:
        """Dapatkan narrative untuk Knowledge page."""
        knowledge = self.build_knowledge()
        return self.narrative.build_from_knowledge(knowledge)

    def build_daily_briefing(self) -> DailyBriefing:
        """Briefing pagi."""
        home = self.build_home()
        activity = self.build_activity()
        work = self.build_work()
        return self.narrative.build_daily_briefing(home, activity, work)

    def build_situation_brief(self) -> SituationBrief:
        """Situasi saat ini."""
        home = self.build_home()
        work = self.build_work()
        knowledge = self.build_knowledge()
        return self.narrative.build_current_situation(home, work, knowledge)

    # ======================================================================
    # HUMAN EXPERIENCE ENGINE
    # ======================================================================

    def detect_situation(self) -> SituationReport:
        """Deteksi situasi terkini — 7 situasi."""
        return self.situation.detect()

    def get_attention_top(self, limit: int = 3) -> list:
        """Top N item paling penting."""
        return self.attention.get_top_items(limit)

    def get_all_attention(self) -> list:
        """Semua item dengan skor perhatian."""
        return self.attention.get_all_scored()

    def build_activity_stories(self) -> list:
        """Event → Cerita."""
        activity = self.build_activity()
        return self.story_builder.build_stories(activity)

    # ======================================================================
    # PRESENTATION / RECOMMENDATION / PREDICTION
    # ======================================================================

    def build_presentation(self, decision: Optional[Decision] = None) -> Presentation:
        """Bangun Presentation untuk Home."""
        sit = self.situation.detect()
        return self.presentation.build(
            situation_str=sit.situation.value,
            attention_score=sit.attention_score,
            decision=decision,
            progress_percent=sit.progress_percent,
            estimated_time=sit.estimated_time,
            detail_level2=sit.detail_level2,
        )

    def get_recommendations(self, limit: int = 5) -> list:
        """'What should happen next?'"""
        sit = self.situation.detect()
        return self.recommendation_engine.get_recommendations(
            situation=sit.situation.value, limit=limit,
        )

    def get_predictions(self, limit: int = 3) -> list:
        """'What happens if nothing is done?'"""
        sit = self.situation.detect()
        return self.prediction_engine.get_predictions(
            situation=sit.situation.value, limit=limit,
        )

    # ======================================================================
    # QUESTION ENGINE — Conversation-first
    # ======================================================================

    def get_live_answer(self, question: str = "",
                         audience_type: str = "") -> HumanAnswer:
        """Satu-satunya cara UI/CLI/Assistant bertanya.

        Desktop: ee.get_live_answer("What's happening?")
        CLI: ee.get_live_answer("Why?", audience_type="developer")
        Assistant: semua jawaban lewat sini.
        """
        return self.question_engine.answer(question, audience_type=audience_type)

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
                answer="Status: {} — {}".format(health.value, msg),
            )

        elif "kenapa" in question_lower or "why" in question_lower:
            # Mengapa? — Format: Reason → Evidence → Decision → Impact → Recommendation
            sit = self.situation.detect()
            lines = []
            lines.append("The system {} because:".format(sit.label.lower().rstrip('.')))
            lines.append("")
            lines.append("  Reason:")
            lines.append("    {}".format(sit.focus_message))
            if sit.focus_detail:
                lines.append("  Evidence:")
                lines.append("    {}".format(sit.focus_detail))
            lines.append("  Decision:")
            lines.append("    {}".format(sit.action_message))
            if sit.detail_level2:
                lines.append("  Impact:")
                for line in sit.detail_level2.split("\n")[:3]:
                    lines.append("    {}".format(line))
            return AssistantAnswer(
                question=question,
                answer="\n".join(lines),
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

        elif "briefing" in question_lower or "pagi" in question_lower or "morning" in question_lower:
            # Daily briefing via Narrative
            brief = self.build_daily_briefing()
            lines = [
                brief.greeting,
                brief.health_summary,
                brief.action_summary,
            ]
            if brief.schedule:
                lines.append("Today's schedule:")
                lines.extend(brief.schedule)
            return AssistantAnswer(
                question=question,
                answer="\n".join(lines),
                details=brief.yesterday_recap,
            )

        elif "situasi" in question_lower or "situation" in question_lower or "current" in question_lower:
            # Situation via Narrative
            sit = self.build_situation_brief()
            lines = [
                sit.summary,
                sit.health_statement,
                sit.incident_statement,
                sit.work_statement,
            ]
            return AssistantAnswer(
                question=question,
                answer="\n".join(lines),
            )

        elif "hari ini" in question_lower or "today" in question_lower or "belajar" in question_lower or "learn" in question_lower:
            # What happened today? + What did SAM learn?
            brief = self.build_daily_briefing()
            lines = [
                brief.greeting,
                brief.health_summary,
                "Yesterday: " + brief.yesterday_recap,
                brief.action_summary,
            ]
            return AssistantAnswer(
                question=question,
                answer="\n".join(lines),
            )

        elif "unfinished" in question_lower or "belum" in question_lower or "pending" in question_lower:
            # Show unfinished work
            work = self.build_work()
            pending_items = [w for w in work.items if w.status == "running" or w.approval_needed]
            if pending_items:
                lines = ["Unfinished work:"]
                for w in pending_items[:5]:
                    status = "Review required" if w.approval_needed else w.status
                    lines.append("  • {} — {}".format(w.title, status))
                return AssistantAnswer(
                    question=question,
                    answer="\n".join(lines),
                )
            return AssistantAnswer(
                question=question,
                answer="All work is completed.",
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
