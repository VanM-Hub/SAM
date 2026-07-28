"""
Conversation — Public API untuk semua interaksi manusia.

Desktop, CLI, Voice, API — semuanya lewat sini.
Tidak ada yang tahu engine di baliknya.

sam.observe() -> Conversation
    .answer("What's happening?")
    .timeline()
    .recommendations()
    .predictions()
    .technical_details()
    .export_json()
    .story()
"""

from typing import Optional, List

from .human_answer import HumanAnswer
from .conversation import ConversationObject
from .conversation_context import ConversationContext
from .intent import InteractionIntent
from .intent_resolver import IntentResolver
from .understanding import UnderstandingEngine as SystemAnalyzer
from .audience import AudienceProfile, get_profile, AudienceType
from .session import MissionSession, SessionManager
from .rca import RootCauseAnalyzer, RootCauseModel, RootCauseReport
from ..render import CLIRenderer, DesktopRenderer, JSONRenderer


INTENT_MAP = {
    "overview": InteractionIntent.OVERVIEW,
    "health": InteractionIntent.HEALTH,
    "user_action": InteractionIntent.USER_ACTION,
    "explain": InteractionIntent.EXPLAIN,
    "changes": InteractionIntent.CHANGES,
    "next_step": InteractionIntent.NEXT_STEP,
    "consequence": InteractionIntent.CONSEQUENCE,
    "technical": InteractionIntent.TECHNICAL,
}


# Lazy import untuk menghindari circular
_runtime_provider_instance = None


def _get_runtime_provider():
    """Dapatkan singleton RuntimeProvider (dengan QueueMonitor internal)."""
    global _runtime_provider_instance
    if _runtime_provider_instance is None:
        from .providers.runtime import RuntimeProvider
        _runtime_provider_instance = RuntimeProvider()
    return _runtime_provider_instance


class Conversation:
    """Satu percakapan — hasil dari sam.observe().

    Semua interaksi pengguna terjadi melalui objek ini.
    Pengguna tidak tahu ada engine, resolver, renderer di belakangnya.
    """

    def __init__(self, understanding: 'SystemAnalyzer',
                 session: SessionManager,
                 audience: AudienceProfile,
                 renderers: dict):
        self._understanding = understanding
        self._session = session
        self._audience = audience
        self._renderers = renderers
        self._context = ConversationContext()

        # Dapatkan ConversationObject saat init
        self._co = understanding.understand()

    # ==================================================================
    # Jawaban pertanyaan
    # ==================================================================

    def answer(self, question: str = "",
               audience_type: str = "") -> HumanAnswer:
        """Jawab pertanyaan manusia."""
        if audience_type:
            self._audience = get_profile(audience_type)
            self._session.set_audience(audience_type)

        return self._answer_text(question)

    def _answer_text(self, question: str) -> HumanAnswer:
        intent = IntentResolver.resolve(question)
        # Auto-track interaksi manusia — bukan developer, SAM sendiri yang track
        from .providers.runtime import RuntimeProvider
        rp = self._understanding.rp
        if rp is None:
            # UnderstandingEngine tidak punya RuntimeProvider, cari via SessionManager
            rp = _get_runtime_provider()
        op_name = "answer.{}".format(intent.value)
        with rp._queue_monitor.track(op_name):
            self._co = self._understanding.understand()
            answer = self._render_for_intent(intent)
        answer.question = question
        answer.intent = intent.value
        self._session.record_interaction(question, intent, answer)
        return answer

    # ==================================================================
    # Intent-specific methods
    # ==================================================================

    def timeline(self) -> HumanAnswer:
        """Kronologi insiden — apa yang terjadi dan kapan."""
        rp = self._understanding.rp or _get_runtime_provider()
        wp = getattr(rp, '_workspace_provider', None) or getattr(rp, 'workspace', None)
        from .timeline import TimelineEngine
        te = TimelineEngine(runtime_provider=rp, workspace_provider=wp)
        entries = te.build(limit=20)

        if not entries:
            return HumanAnswer(
                title="Nothing significant has changed.",
                summary="No timeline data available.",
                severity="information",
                icon="\u2705",
                badges=[(self._audience.label, "#505060")],
            )

        # Group by severity
        critical = [e for e in entries if e.severity == "critical"]
        warnings = [e for e in entries if e.severity == "warning"]

        timeline_text = "\n".join(e.to_text() for e in entries)
        severity = "warning" if warnings else ("critical" if critical else "information")

        return HumanAnswer(
            title="Timeline: {} events.".format(len(entries)),
            summary=entries[-1].to_text() if entries else "",
            sections=[("Timeline", timeline_text)],
            severity=severity,
            icon="\U0001f552",
            badges=[(self._audience.label, "#505060")],
        )

    def story(self) -> HumanAnswer:
        """Cerita operasional."""
        return self._answer_intent(InteractionIntent.OVERVIEW)

    def recommendations(self) -> HumanAnswer:
        """Rekomendasi actionable — dengan reason, priority, impact, urgency, expected outcome."""
        rp = self._understanding.rp or _get_runtime_provider()
        wp = getattr(rp, '_workspace_provider', None) or getattr(rp, 'workspace', None)
        from .anomaly import AnomalyDetector
        from .recommend import RecommendationEngine

        ad = AnomalyDetector(runtime_provider=rp, workspace_provider=wp) if rp else None
        re = RecommendationEngine(
            anomaly_detector=ad,
            runtime_provider=rp,
            workspace_provider=wp,
        )
        actionable = re.recommend_all()

        if not actionable:
            return HumanAnswer(
                title="No specific recommendation.",
                summary="Everything is operating normally.",
                severity="information",
                icon="\u2705",
                badges=[(self._audience.label, "#505060")],
            )

        sections = []
        for r in actionable[:5]:
            lines = [
                "Reason: {}".format(r.reason),
                "Priority: {} | Impact: {}".format(r.priority, r.impact),
                "Urgency: {} | Expected: {}".format(r.urgency, r.expected_outcome),
            ]
            sections.append((r.action[:50], "\n".join(lines)))

        return HumanAnswer(
            title="{} recommendation(s).".format(len(actionable)),
            summary=actionable[0].to_text(),
            sections=sections,
            actions=[r.action for r in actionable[:3]],
            severity="warning" if any(r.priority in ("critical", "high") for r in actionable) else "information",
            icon="\U0001f4a1",
            badges=[(self._audience.label, "#505060")],
        )

    def predictions(self) -> HumanAnswer:
        """Apa yang terjadi jika tidak ada tindakan."""
        return self._answer_intent(InteractionIntent.CONSEQUENCE)

    def technical_details(self) -> HumanAnswer:
        """Detail teknis."""
        return self._answer_intent(InteractionIntent.TECHNICAL)

    def health(self) -> HumanAnswer:
        """Apakah semuanya baik-baik saja."""
        return self._answer_intent(InteractionIntent.HEALTH)

    def actions(self) -> HumanAnswer:
        """Tindakan yang perlu dilakukan."""
        return self._answer_intent(InteractionIntent.USER_ACTION)

    def explain(self) -> HumanAnswer:
        """Kenapa ini terjadi."""
        return self._answer_intent(InteractionIntent.EXPLAIN)

    def anomalies(self) -> HumanAnswer:
        """Apa yang abnormal? Deteksi anomali real-time."""

    def forecast(self) -> HumanAnswer:
        """Prediksi — apa yang akan terjadi jika tidak ada tindakan."""
        rp = self._understanding.rp or _get_runtime_provider()
        wp = getattr(rp, '_workspace_provider', None) or getattr(rp, 'workspace', None)
        from .forecast import ForecastEngine
        fe = ForecastEngine(runtime_provider=rp, workspace_provider=wp)
        forecasts = fe.forecast_all()

        if not forecasts or (len(forecasts) == 1 and "unavailable" in forecasts[0].prediction):
            return HumanAnswer(
                title="Forecast unavailable.",
                summary="Need additional historical observations.",
                severity="information",
                icon="\U0001f52e",
                badges=[(self._audience.label, "#505060")],
            )

        sections = []
        for f in forecasts:
            lines = [f.to_text()]
            if f.supporting_evidence:
                for e in f.supporting_evidence:
                    lines.append("  - {}".format(e))
            sections.append((f.metric.replace("_", " ").title(), "\n".join(lines)))

        return HumanAnswer(
            title="{} forecast(s) available.".format(len(forecasts)),
            summary=forecasts[0].to_text() if forecasts else "No forecast.",
            sections=sections,
            severity="information",
            icon="\U0001f4c8",
            badges=[(self._audience.label, "#505060")],
        )
        rp = self._understanding.rp or _get_runtime_provider()
        wp = getattr(rp, '_workspace_provider', None) or getattr(rp, 'workspace', None)
        from .anomaly import AnomalyDetector
        ad = AnomalyDetector(runtime_provider=rp, workspace_provider=wp)
        anomalies = ad.detect_all()

        if not anomalies:
            return HumanAnswer(
                title="No anomalies detected.",
                summary="All systems operating normally.",
                severity=self._co.situation_severity,
                icon="\u2705",
                badges=[(self._audience.label, "#505060")],
            )

        # Group by severity
        crit = [a for a in anomalies if a.severity == "critical"]
        warn = [a for a in anomalies if a.severity == "warning"]
        info = [a for a in anomalies if a.severity == "information"]

        sections = []
        if crit:
            sections.append(("Critical", "\n".join("[{}] {} — {:.0f}%".format(a.type, a.detail or a.evidence[0] if a.evidence else "", a.confidence * 100) for a in crit)))
        if warn:
            sections.append(("Warnings", "\n".join("[{}] {} — {:.0f}%".format(a.type, a.detail or a.evidence[0] if a.evidence else "", a.confidence * 100) for a in warn)))
        if info:
            sections.append(("Info", "\n".join("[{}] {} — {:.0f}%".format(a.type, a.detail or a.evidence[0] if a.evidence else "", a.confidence * 100) for a in info)))

        severity = "critical" if crit else ("warning" if warn else "information")
        return HumanAnswer(
            title="{} anomaly/anomalies detected.".format(len(anomalies)),
            summary="{} critical, {} warning, {} info".format(len(crit), len(warn), len(info)),
            sections=sections,
            severity=severity,
            icon="\u26a0" if warn or crit else "\u2705",
            badges=[(self._audience.label, "#505060")],
        )

    # ==================================================================
    # RCA — Root Cause Analysis
    # ==================================================================

    def why(self, question: str = "") -> HumanAnswer:
        """Analisis akar penyebab — evidence-based.

        Args:
            question: "Why is CPU high?" or "What caused this?"

        Returns:
            HumanAnswer dengan root cause atau penjelasan insufficient evidence.
        """
        # Dapatkan provider dari understanding
        rp = self._understanding.rp or _get_runtime_provider()
        wp = getattr(rp, '_workspace_provider', None) or getattr(rp, 'workspace', None)

        # Bangun RCA
        rca = RootCauseAnalyzer(runtime_provider=rp, workspace_provider=wp)
        model = rca.analyze(question or "Why is this happening?", context={
            "observed_event": self._co.summary if hasattr(self._co, 'summary') else "",
        })
        report = rca.to_report(model)

        # Auto-track sebagai operasi RCA
        op_name = "rca.{}".format(question[:30] if question else "general")
        with rp._queue_monitor.track(op_name):
            pass  # sudah dilacak

        # Bangun HumanAnswer
        if report.root_cause:
            sections = [("Evidence", "\n".join(report.supporting_evidence))]
            if report.missing_observations:
                sections.append(("Missing", "\n".join(report.missing_observations)))
            return HumanAnswer(
                title="Root cause identified.",
                summary=report.root_cause,
                sections=sections,
                predictions=["Confidence: {:.0f}%".format(report.confidence * 100)],
                severity=self._co.situation_severity,
                icon="\U0001f50d",
                badges=[(self._audience.label, "#505060")],
            )
        else:
            sections = []
            if report.missing_observations:
                sections.append(("Additional observations required", "\n".join(report.missing_observations)))
            return HumanAnswer(
                title="Insufficient evidence.",
                summary="Cannot determine root cause with available evidence.",
                sections=sections,
                severity="information",
                icon="\u2753",
                badges=[(self._audience.label, "#505060")],
            )

    # ==================================================================
    # Render
    # ==================================================================

    def render_cli(self, answer: HumanAnswer) -> str:
        return self._renderers["cli"].render(answer)

    def render_desktop(self, answer: HumanAnswer) -> dict:
        return self._renderers["desktop"].render(answer)

    def security_status(self) -> HumanAnswer:
        """Observasi keamanan — permission, credential, certificate, secret, policy, signature."""
        rp = self._understanding.rp or _get_runtime_provider()
        wp = getattr(rp, '_workspace_provider', None) or getattr(rp, 'workspace', None)
        from .security import SecurityObserver
        so = SecurityObserver(workspace_provider=wp, runtime_provider=rp)
        observations = so.observe_all()

        if not observations:
            return HumanAnswer(
                title="No security concerns detected.",
                summary="All security checks passed.",
                severity="information",
                icon="\u2705",
                badges=[(self._audience.label, "#505060")],
            )

        sections = []
        crit = [o for o in observations if o.severity == "critical"]
        warn = [o for o in observations if o.severity == "warning"]
        info = [o for o in observations if o.severity == "information"]

        for o in crit:
            sections.append((o.category, o.to_text()))
        for o in warn:
            sections.append((o.category, o.to_text()))
        for o in info:
            sections.append((o.category, o.to_text()))

        severity = "critical" if crit else ("warning" if warn else "information")
        return HumanAnswer(
            title="{} security observation(s).".format(len(observations)),
            summary=so.get_summary(),
            sections=sections[:10],
            severity=severity,
            icon="\U0001f6e1" if not crit else "\u26a0",
            badges=[(self._audience.label, "#505060")],
        )

    # ==================================================================
    # Decision Layer — Sprint 3
    # ==================================================================

    def decisions(self) -> HumanAnswer:
        """Apa yang harus dilakukan? Proposal keputusan dari SAM."""
        self._co = self._understanding.understand()

        if not self._co.decisions:
            return HumanAnswer(
                title="No decisions required.",
                summary="All systems operating normally — no action needed.",
                severity="information",
                icon="✅",
                badges=[(self._audience.label, "#505060")],
            )

        dd = self._co.decision_details or {}
        sections = []
        proposals = dd.get("proposals", [])
        for p in proposals:
            lines = []
            lines.append("Confidence: {:.0f}%".format(p.get("confidence", 0) * 100))
            lines.append("Reason: {}".format(p.get("reason", "")))
            if p.get("uncertainty"):
                lines.append("Uncertainty: {}".format(p["uncertainty"]))
            if p.get("missing_information"):
                lines.append("Missing: {}".format("; ".join(p["missing_information"])))
            if p.get("blocking_conditions"):
                lines.append("Blocked: {}".format("; ".join(p["blocking_conditions"])))
            sections.append((p.get("decision", "Unknown")[:60], "\n".join(lines)))

        severity = "warning" if proposals else "information"
        return HumanAnswer(
            title="{} decision proposal(s).".format(len(proposals)),
            summary=proposals[0].get("decision", "") if proposals else "",
            sections=sections,
            severity=severity,
            icon="⚙",
            badges=[(self._audience.label, "#505060")],
        )

    def decision_impact(self, decision_index: int = 0) -> HumanAnswer:
        """Apa dampak dari keputusan ini?"""
        self._co = self._understanding.understand()

        if not self._co.impact_details:
            return HumanAnswer(
                title="Impact assessment unavailable.",
                summary="Need anomaly detection data to assess impact.",
                severity="information",
                icon="✅",
                badges=[(self._audience.label, "#505060")],
            )

        assessments = self._co.impact_details.get("assessments", [])
        if not assessments:
            return HumanAnswer(
                title="No impact assessments.",
                severity="information",
                icon="✅",
                badges=[(self._audience.label, "#505060")],
            )

        idx = min(decision_index, len(assessments) - 1)
        a = assessments[idx]
        lines = [
            "Expected outcome: {}".format(a.get("expected_outcome", "Unknown")),
        ]
        if a.get("possible_interruption"):
            lines.append("Interruption: {}".format(a["possible_interruption"]))
        if a.get("estimated_recovery"):
            lines.append("Recovery: {}".format(a["estimated_recovery"]))
        if a.get("rollback_possibility"):
            lines.append("Rollback: {}".format(a["rollback_possibility"]))
        lines.append("Risk: {}".format(a.get("risk", "Unknown")))
        lines.append("Confidence: {:.0f}%".format(a.get("confidence", 0) * 100))

        suff = a.get("is_sufficient", True)
        if not suff:
            lines.append("\nInsufficient evidence for accurate impact assessment.")

        sev = "warning" if a.get("risk", "").lower() in ("high", "medium", "critical") else "information"
        return HumanAnswer(
            title="Impact: {}".format(a.get("decision", "")[:80]),
            summary=a.get("expected_outcome", "Unknown"),
            sections=[("Impact Analysis", "\n".join(lines))],
            severity=sev,
            icon="\U0001f52e",
            badges=[(self._audience.label, "#505060")],
        )

    def decision_alternatives(self) -> HumanAnswer:
        """Apa alternatifnya? Recommended, Alternative, Emergency."""
        self._co = self._understanding.understand()

        if not self._co.alternatives_details:
            return HumanAnswer(
                title="No alternatives generated.",
                summary="No anomalies detected — no alternatives needed.",
                severity="information",
                icon="✅",
                badges=[(self._audience.label, "#505060")],
            )

        alts = self._co.alternatives_details.get("alternatives", [])
        if not alts:
            return HumanAnswer(
                title="No alternatives.",
                severity="information",
                icon="✅",
                badges=[(self._audience.label, "#505060")],
            )

        sections = []
        for alt in alts:
            rec = alt.get("recommended", {})
            alt_text = alt.get("alternative", {})
            emerg = alt.get("emergency", {})

            lines = ["Recommended: {} ({:.0f}%)".format(
                rec.get("decision", ""), rec.get("confidence", 0) * 100
            )]
            if alt_text:
                lines.append("Alternative: {} ({:.0f}%)".format(
                    alt_text.get("decision", ""), alt_text.get("confidence", 0) * 100
                ))
            if emerg:
                lines.append("Emergency: {} ({:.0f}%)".format(
                    emerg.get("decision", ""), emerg.get("confidence", 0) * 100
                ))

            sections.append((rec.get("decision", "")[:60], "\n".join(lines)))

        return HumanAnswer(
            title="{} alternative set(s) available.".format(len(alts)),
            summary=sections[0][1][:120] if sections else "",
            sections=sections,
            severity="information",
            icon="⚙",
            badges=[(self._audience.label, "#505060")],
        )

    def action_center(self) -> HumanAnswer:
        """Action Center — approval status."""
        self._co = self._understanding.understand()

        pending = self._co.approval_pending_count
        approved = self._co.approval_approved_count
        rejected = self._co.approval_rejected_count

        sections = []
        sections.append(("Summary", "Pending: {} | Approved: {} | Rejected: {}".format(
            pending, approved, rejected
        )))

        # Get pending items from store
        try:
            from .approval import ApprovalWorkflow
            aw = ApprovalWorkflow()
            pending_items = aw.get_pending()
            approved_items = aw.get_approved()
            rejected_items = aw.get_rejected()

            if pending_items:
                lines = []
                for item in pending_items[:5]:
                    lines.append(item.summary_text())
                sections.append(("Pending Decisions", "\n".join(lines)))

            if approved_items:
                lines = []
                for item in approved_items[:5]:
                    lines.append(item.summary_text())
                sections.append(("Approved", "\n".join(lines)))

            if rejected_items:
                lines = []
                for item in rejected_items[:5]:
                    lines.append(item.summary_text())
                sections.append(("Rejected", "\n".join(lines)))
        except Exception:
            pass

        sev = "attention" if pending > 0 else "information"
        return HumanAnswer(
            title="Action Center — {} pending.".format(pending),
            summary="{} pending approval(s), {} approved, {} rejected.".format(pending, approved, rejected),
            sections=sections,
            actions=["Show pending", "Show history"],
            severity=sev,
            icon="⚙",
            badges=[(self._audience.label, "#505060")],
        )

    def config_drift(self) -> HumanAnswer:
        """Deteksi perubahan konfigurasi."""
        rp = self._understanding.rp or _get_runtime_provider()
        wp = getattr(rp, '_workspace_provider', None) or getattr(rp, 'workspace', None)
        from .config_drift import ConfigurationDriftDetector
        cdd = ConfigurationDriftDetector(workspace_provider=wp)
        changes = cdd.observe()

        if not changes:
            return HumanAnswer(
                title="No configuration drift detected.",
                summary="Configuration is consistent.",
                severity="information",
                icon="\u2705",
                badges=[(self._audience.label, "#505060")],
            )

        sections = []
        for c in changes:
            sections.append((c.path, c.to_text()))

        has_secret = any(c.change_type == "secret_changed" for c in changes)
        return HumanAnswer(
            title="{} configuration change(s) detected.".format(len(changes)),
            summary=changes[0].to_text(),
            sections=sections,
            severity="warning" if has_secret else "information",
            icon="\u26a0" if has_secret else "\U0001f504",
            badges=[(self._audience.label, "#505060")],
        )

    def deployment_status(self) -> HumanAnswer:
        """Status deployment — apakah berhasil, apa yang berubah."""
        from .deployment import DeploymentProvider
        dp = DeploymentProvider()
        summary = dp.get_summary()
        latest = dp.get_latest()

        sections = []
        if latest and latest.changes:
            sections.append(("Changes", "\n".join(latest.changes)))
        if latest and latest.runtime_impact:
            sections.append(("Runtime Impact", "\n".join(latest.runtime_impact)))

        all_deploys = dp.get_all()
        if len(all_deploys) > 1:
            history = "\n".join(d.to_text() for d in all_deploys)
            sections.append(("History", history))

        severity = "critical" if latest and latest.status == "failed" else (
            "attention" if latest and latest.status == "rollback" else (
                "information"
            )
        )

        return HumanAnswer(
            title=summary,
            summary=summary,
            sections=sections,
            severity=severity,
            icon="\U0001f680" if latest and latest.status in ("success", "in_progress") else "\u26a0",
            badges=[(self._audience.label, "#505060")],
        )

    def export_json(self, answer: Optional[HumanAnswer] = None) -> dict:
        ans = answer or self._render_for_intent(InteractionIntent.OVERVIEW)
        return self._renderers["json"].render(ans)

    # ==================================================================
    # Internal
    # ==================================================================

    def _answer_intent(self, intent: InteractionIntent) -> HumanAnswer:
        self._co = self._understanding.understand()
        answer = self._render_for_intent(intent)
        answer.intent = intent.value
        return answer

    def _render_for_intent(self, intent: InteractionIntent) -> HumanAnswer:
        iv = intent.value
        # Delegasi ke internal renderer
        if iv == "overview":
            return self._render_overview()
        elif iv == "health":
            return self._render_health()
        elif iv == "user_action":
            return self._render_user_action()
        elif iv == "explain":
            return self._render_explain()
        elif iv == "changes":
            return self._render_changes()
        elif iv == "next_step":
            return self._render_next_step()
        elif iv == "consequence":
            return self._render_consequence()
        elif iv == "technical":
            return self._render_technical()
        return self._render_overview()

    def _render_overview(self) -> HumanAnswer:
        co, p = self._co, self._audience
        sections, cards, actions = [], [], []
        if p.technical_level >= 2 and co.activity_changes:
            sections.append(("Recent Changes", "\n".join(co.activity_changes[:3])))
        if co.user_action_needed and "No action" not in co.user_action_needed:
            actions.append(co.user_action_needed)
        if co.recommendations and p.verbosity != "brief":
            sections.append(("Recommendations", "\n".join(co.recommendations)))
        if co.predictions and p.show_predictions:
            sections.append(("Predictions", "\n".join(co.predictions)))
        if co.sam_action:
            cards.append(("\u2699", "SAM", co.sam_action))
        if p.show_evidence and co.evidence:
            sections.append(("Evidence", "\n".join(co.evidence[:2])))
        icons = {"critical": "\U0001f6a8", "action_required": "\u26a0", "attention": "\u26a0", "information": "\u2705"}
        return HumanAnswer(title=co.mission_condition, summary=co.mission_activity,
                           sections=sections, cards=cards, actions=actions,
                           severity=co.situation_severity,
                           priority=1 if co.situation_severity in ("critical", "action_required") else 3,
                           icon=icons.get(co.situation_severity, "\u2705"),
                           badges=[(p.label, "#505060")])

    def _render_health(self) -> HumanAnswer:
        sev = self._co.situation_severity
        if sev in ("information", "success"):
            return HumanAnswer(title="Everything is operating normally.",
                               summary="No issues detected. Monitoring continues.",
                               severity=sev, icon="\u2705",
                               badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title=self._co.mission_condition, summary=self._co.mission_activity,
                           severity=self._co.situation_severity, icon="\u26a0",
                           badges=[(self._audience.label, "#505060")])

    def _render_user_action(self) -> HumanAnswer:
        acts = []
        if self._co.user_action_needed and "No action" not in self._co.user_action_needed:
            acts.append(self._co.user_action_needed)
        acts.extend(self._co.recommendations[:3])
        return HumanAnswer(title=self._co.user_action_needed, summary=self._co.mission_activity,
                           actions=acts, severity=self._co.situation_severity,
                           icon="\u2757", badges=[(self._audience.label, "#505060")])

    def _render_explain(self) -> HumanAnswer:
        sections = []

        # RCA — jika tersedia, pakai RootCauseReport
        if self._co.root_cause:
            rc = self._co.root_cause
            if rc.get("root_cause"):
                sections.append(("Root Cause", rc["root_cause"]))
                if rc.get("supporting_evidence"):
                    sections.append(("Evidence", "\n".join(rc["supporting_evidence"][:5])))
            else:
                sections.append(("Insufficient Evidence", rc.get("summary", "")))
                if rc.get("missing_observations"):
                    sections.append(("Additional Observations Required", "\n".join(rc["missing_observations"])))
            summary = rc.get("root_cause") or rc.get("summary", "No specific reason found.")
            return HumanAnswer(title=summary[:120], summary=summary, sections=sections,
                               severity=self._co.situation_severity, icon="\U0001f50d",
                               badges=[(self._audience.label, "#505060")])

        # Fallback — tanpa RCA
        if self._audience.show_evidence and self._co.evidence:
            sections.append(("Evidence", "\n".join(self._co.evidence[:3])))
        if self._co.facts:
            sections.append(("Facts", "\n".join(self._co.facts[:2])))
        summary = self._co.evidence[0] if self._co.evidence else "No specific reason found."
        return HumanAnswer(title=summary[:120], summary=summary, sections=sections,
                           severity=self._co.situation_severity, icon="\u2753",
                           badges=[(self._audience.label, "#505060")])

    def _render_changes(self) -> HumanAnswer:
        if self._co.activity_changes:
            s = "\n".join(self._co.activity_changes)
            return HumanAnswer(title="Recent changes." if len(self._co.activity_changes) > 1 else self._co.activity_changes[0],
                               summary=s, sections=[("Changes", s)],
                               icon="\U0001f504", badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title="Nothing significant has changed.", summary="Everything is operating normally.",
                           icon="\u2705", badges=[(self._audience.label, "#505060")])

    def _render_next_step(self) -> HumanAnswer:
        if self._co.recommendations:
            return HumanAnswer(title="Recommendation available.", summary=self._co.recommendations[0],
                               sections=[("Recommendations", "\n".join(self._co.recommendations))],
                               predictions=self._co.predictions[:1], icon="\U0001f4a1",
                               badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title="No specific recommendation.", summary="Everything is operating normally.",
                           icon="\u2705", badges=[(self._audience.label, "#505060")])

    def _render_consequence(self) -> HumanAnswer:
        if self._co.risks:
            return HumanAnswer(title=self._co.risks[0],
                               summary=self._co.predictions[0] if self._co.predictions else self._co.risks[0],
                               sections=[("Risks", "\n".join(self._co.risks))],
                               predictions=self._co.predictions, actions=self._co.recommendations[:2],
                               icon="\U0001f52e", badges=[(self._audience.label, "#505060")])
        return HumanAnswer(title="No negative impact expected.", summary="Everything is operating normally.",
                           icon="\u2705", badges=[(self._audience.label, "#505060")])

    def _render_technical(self) -> HumanAnswer:
        return HumanAnswer(title=self._co.mission_condition,
                           details=self._co.technical_details or "No technical details available.",
                           sections=[("Technical", self._co.technical_details)] if self._co.technical_details else [],
                           icon="\u2699", badges=[(self._audience.label, "#505060")])


class SAM:
    """Entry point publik — satu-satunya cara berinteraksi dengan SAM.

    sam = SAM()
    conversation = sam.observe()
    answer = conversation.answer("What's happening?")
    """

    def __init__(self, experience_engine=None):
        self._ee = experience_engine
        self._runtime_provider = _get_runtime_provider()
        self._understanding = SystemAnalyzer(experience_engine, self._runtime_provider)
        self._session = SessionManager()
        self._renderers = {
            "cli": CLIRenderer(),
            "desktop": DesktopRenderer(),
            "json": JSONRenderer(),
        }
        self._started = False

    def observe(self, audience_type: str = AudienceType.ADMINISTRATOR,
                mission_target: str = "Workspace") -> Conversation:
        """Mulai percakapan — amati keadaan sistem.

        Ini adalah satu-satunya cara memulai.
        Tidak ada engine, resolver, renderer yang terlihat.
        """
        profile = get_profile(audience_type)
        self._session.start_session(audience_type, mission_target)
        return Conversation(
            understanding=self._understanding,
            session=self._session,
            audience=profile,
            renderers=self._renderers,
        )

    # ==================================================================
    # Runtime provider lifecycle
    # ==================================================================

    @property
    def runtime(self):
        """Akses ke RuntimeProvider (untuk testing/integrasi)."""
        return self._runtime_provider

    async def start_runtime(self, telemetry=None):
        """Mulai RuntimeProvider background polling + auto-hook QueueMonitor."""
        self._started = True

        # Hook QueueMonitor ke TelemetryService — otomatis!
        if telemetry:
            self._runtime_provider._queue_monitor.hook_telemetry(telemetry)

        await self._runtime_provider.start()

    async def stop_runtime(self):
        """Hentikan RuntimeProvider."""
        await self._runtime_provider.stop()
        self._started = False
