"""
SystemAnalyzer — Sintesis ConversationObject dari semua sumber.

Input:
  Telemetry
  SituationAnalyzer
  PresentationRenderer
  Knowledge
  Protection
  Work
  Mission

Output:
  ConversationObject — satu objek, sumber kebenaran.

Tidak ada logika naratif di sini.
Hanya sintesis: mengumpulkan, memprioritaskan, menyusun.
"""

from dataclasses import dataclass, field
from typing import Optional, List

from .conversation import ConversationObject


# Backward-compat alias (Engine rename: UnderstandingEngine → SystemAnalyzer)
UnderstandingEngine = None  # resolved below


class SystemAnalyzer:
    """Sintesis ConversationObject — keadaan operasional yang dipahami manusia.

    BUKAN pembuat kalimat.
    BUKAN narator.
    Ini adalah otak yang memahami apa yang terjadi.
    """

    def __init__(self, experience_engine=None, runtime_provider=None):
        self.ee = experience_engine
        self.rp = runtime_provider  # RuntimeProvider instance

    def understand(self) -> ConversationObject:
        """Pahami keadaan sistem → ConversationObject.

        Satu panggilan. Satu objek. Semua yang diketahui.
        """
        try:
            sit = None
            pres = None
            recs = []
            preds = []
            stories = []
            work_items = []

            if self.ee:
                if hasattr(self.ee, 'situation'):
                    try:
                        sit = self.ee.situation.detect()
                    except Exception:
                        pass

                try:
                    pres = self.ee.build_presentation()
                except Exception:
                    pass

                try:
                    recs = self.ee.get_recommendations(limit=3)
                except Exception:
                    pass

                try:
                    preds = self.ee.get_predictions(limit=2)
                except Exception:
                    pass

                try:
                    stories = self.ee.build_activity_stories() or []
                except Exception:
                    pass

                try:
                    work = self.ee.build_work()
                    if work and hasattr(work, 'items') and work.items:
                        work_items = [getattr(i, 'title', str(i)) for i in work.items[:3]]
                except Exception:
                    pass

            # ============================================================
            # SITUATION
            # ============================================================
            sit_value = sit.situation.value if sit else "everything_healthy"
            sit_label = sit.situation.value.replace("_", " ").title() if sit else "Everything Healthy"

            # Map severity
            severity_map = {
                "action_required": "critical",
                "needs_attention": "attention",
                "waiting_approval": "action_required",
                "deployment_running": "information",
                "recovering": "attention",
                "learning": "information",
                "everything_healthy": "information",
                "error": "critical",
            }
            severity = severity_map.get(sit_value, "information")

            # ============================================================
            # REASON — dari SituationReport.focus_message atau description
            # ============================================================
            sit_reason = getattr(sit, 'description', '') or getattr(sit, 'focus_message', '')

            # ============================================================
            # MISSION
            # ============================================================
            mission_condition = pres.system_condition if pres else "Operating normally."
            mission_activity = pres.current_activity if pres else "Monitoring continues."

            # ============================================================
            # SAM ACTION — hanya jika SAM bertindak
            # ============================================================
            sam_action = pres.sam_action if pres else ""
            user_action = pres.user_action_needed if pres else "No action required."

            # ============================================================
            # FACTS — termasuk runtime data dari RuntimeProvider
            # ============================================================
            facts = []
            if sit:
                facts.append("Situation: {}.".format(sit_label))
                if sit_reason:
                    facts.append("Reason: {}.".format(sit_reason))
            if work_items:
                facts.append("Active work: {} item(s).".format(len(work_items)))

            # Runtime data (Live Telemetry)
            runtime_snapshot = None
            if self.rp:
                try:
                    runtime_snapshot = self.rp.get_latest()
                except Exception:
                    pass

            if runtime_snapshot:
                cpu = runtime_snapshot.cpu_percent
                mem = runtime_snapshot.memory_percent
                queue = runtime_snapshot.queue_depth
                tp = runtime_snapshot.throughput
                active = runtime_snapshot.active_operations
                avg_lat = runtime_snapshot.avg_latency_ms
                qstatus = runtime_snapshot.queue_status

                # Queue-based summary — bisa jelaskan idle/processing/overloaded/growing/healthy
                qstatus_map = {
                    "idle": "System idle",
                    "healthy": "Queue healthy, {} pending".format(queue),
                    "processing": "Processing {} operation(s)".format(active),
                    "growing": "Queue growing: {} pending".format(queue),
                    "overloaded": "High workload: {} active, {} pending".format(active, queue),
                }
                queue_summary = qstatus_map.get(qstatus, "System idle")

                facts.append("CPU: {:.1f}% | Memory: {:.1f}% | {}".format(
                    cpu, mem, queue_summary
                ))

                # Queue detail facts
                if qstatus != "idle":
                    facts.append("Throughput: {:.1f} ops/s | Latency: avg {:.0f}ms".format(tp, avg_lat))

            # Workspace data (OP-65)
            ws = None
            if self.rp:
                try:
                    ws = self.rp.get_workspace()
                    if ws:
                        ws_facts = ws.get_facts()
                        facts.extend(ws_facts)
                        ws_recs = ws.get_recommendations()
                        recs.extend([r for r in ws_recs if r not in recs])
                        ws_preds = ws.get_predictions()
                        preds.extend([p for p in ws_preds if p not in preds])
                except Exception:
                    pass

            # ============================================================
            # ANOMALY DETECTION (OP-73)
            # ============================================================
            anomaly_evidence = []
            if self.rp:
                try:
                    from .anomaly import AnomalyDetector
                    ad = AnomalyDetector(
                        runtime_provider=self.rp,
                        workspace_provider=(
                            getattr(self.rp, '_workspace_provider', None)
                            if self.rp else None
                        ),
                    )
                    anomalies = ad.detect_all()
                    for a in anomalies:
                        anomaly_evidence.append(
                            "[{}] {} — {}".format(a.severity.upper(), a.type, a.detail or a.evidence[0] if a.evidence else "")
                        )
                except Exception:
                    pass

            # ============================================================
            # EVIDENCE
            # ============================================================
            evidence = []
            if sit and sit_reason:
                evidence.append(sit_reason)
            if anomaly_evidence:
                evidence.extend(anomaly_evidence[:5])
            if not evidence:
                evidence.append("All systems operating normally.")

            # ============================================================
            # ACTIONS
            # ============================================================
            user_actions = []
            if user_action and "No action" not in user_action:
                user_actions.append(user_action)
            if recs:
                for r in recs[:3]:
                    if isinstance(r, str):
                        user_actions.append(r)
                    elif hasattr(r, 'priority') and r.priority > 10:
                        user_actions.append(r.display())

            # ============================================================
            # RISKS + PREDICTIONS
            # ============================================================
            risks = []
            predictions_list = []
            for p in preds:
                if isinstance(p, str):
                    if p not in predictions_list:
                        predictions_list.append(p)
                elif hasattr(p, 'risk') and p.risk and p.risk != "None":
                    risks.append("{} — Risk: {}".format(p.event, p.risk))
                    predictions_list.append(p.display())

            # ============================================================
            # RECOMMENDATIONS
            # ============================================================
            recommendations_list = []
            for r in recs:
                if isinstance(r, str):
                    if r not in recommendations_list:
                        recommendations_list.append(r)
                elif hasattr(r, 'priority') and r.priority > 10:
                    recommendations_list.append(r.display())

            # ============================================================
            # ACTIVITY
            # ============================================================
            activity_changes = [s.title for s in stories[:5]]

            # ============================================================
            # TECHNICAL — termasuk detail runtime + workspace
            # ============================================================
            tech = pres.detail if pres else ""

            # Build workspace technical details (selalu, jika ada provider)
            ws_tech_str = ""
            if ws:
                ws_lines = ["--- Workspace ---"]
                if ws.disk.total_gb > 0:
                    ws_lines.append("Disk: {:.1f} GB / {:.1f} GB ({:.1f}%)".format(
                        ws.disk.used_gb, ws.disk.total_gb, ws.disk.percent
                    ))
                ws_lines.append("Database: {}".format(ws.database.status))
                if ws.cache.path:
                    ws_lines.append("Cache: {:.1f} MB ({})".format(ws.cache.size_mb, ws.cache.file_count))
                if ws.temp.count > 0:
                    ws_lines.append("Temp files: {} ({:.1f} MB)".format(ws.temp.count, ws.temp.size_mb))
                ws_tech_str = "\n".join(ws_lines)

            if runtime_snapshot:
                cpu_detail = "{} ({:.1f}% avg, {} cores)".format(
                    runtime_snapshot.cpu_percent,
                    sum(runtime_snapshot.cpu.per_cpu) / max(len(runtime_snapshot.cpu.per_cpu), 1),
                    runtime_snapshot.cpu.count,
                )
                mem_detail = "{} ({:.1f}% of {} MB)".format(
                    _fmt_bytes(runtime_snapshot.memory.rss),
                    runtime_snapshot.memory_percent,
                    int(runtime_snapshot.memory.total / 1024 / 1024),
                )
                uptime = runtime_snapshot.uptime_seconds
                uptime_str = "{:02d}h {:02d}m".format(int(uptime // 3600), int((uptime % 3600) // 60))

                # Queue stats
                queue_depth = runtime_snapshot.queue_depth
                active_ops = runtime_snapshot.active_operations
                throughput = runtime_snapshot.throughput
                avg_lat = runtime_snapshot.avg_latency_ms
                peak_lat = runtime_snapshot.peak_latency_ms
                total_completed = runtime_snapshot.total_completed

                tech_lines = ["--- Runtime ---"]
                tech_lines.append("CPU: {}".format(cpu_detail))
                tech_lines.append("Memory: {}".format(mem_detail))
                tech_lines.append("Uptime: {}".format(uptime_str))
                tech_lines.append("")
                tech_lines.append("--- Queue ---")
                tech_lines.append("Depth: {} | Active: {} | Throughput: {:.1f} ops/s".format(
                    queue_depth, active_ops, throughput
                ))
                tech_lines.append("Latency: avg {:.0f}ms | peak {:.0f}ms".format(avg_lat, peak_lat))
                tech_lines.append("Operations last minute: {}".format(total_completed))
                tech_lines.append("Total completed: {}".format(runtime_snapshot.total_completed))

                if pres and pres.detail:
                    tech_lines.append("")
                    tech_lines.append(pres.detail)

                # Merge workspace technical
                if ws_tech_str:
                    tech_lines.append("")
                    tech_lines.append(ws_tech_str)

                tech = "\n".join(tech_lines)
            elif ws_tech_str:
                tech = ws_tech_str

            # ============================================================
            # ATTENTION
            # ============================================================
            att_label = pres.attention_label if pres else "Normal"
            att_score = 20
            if att_label == "Immediate":
                att_score = 100
            elif att_label == "Soon":
                att_score = 80
            elif att_label == "Normal":
                att_score = 50

            # ============================================================
            # DECISION LAYER — Sprint 3 (OP-81 s.d. OP-85)
            # ============================================================
            decision_package = None
            impact_package = None
            alternatives_package = None
            approval_pending = 0
            approval_approved = 0
            approval_rejected = 0
            decision_texts = []

            if self.rp:
                try:
                    from .decision import DecisionPolicy
                    from .impact import ImpactAnalyzer
                    from .alternatives import AlternativesEngine
                    from .anomaly import AnomalyDetector

                    ad = AnomalyDetector(
                        runtime_provider=self.rp,
                        workspace_provider=(
                            getattr(self.rp, '_workspace_provider', None)
                            if self.rp else None
                        ),
                    )

                    # Decision Policy
                    dp = DecisionPolicy(runtime_provider=self.rp)
                    decision_package = dp.evaluate_all(anomaly_detector=ad)
                    if decision_package and decision_package.proposals:
                        decision_texts = [p.to_text()[:120] for p in decision_package.proposals[:5]]

                        # Impact Analysis
                        ia = ImpactAnalyzer(runtime_provider=self.rp)
                        impact_package = ia.analyze_all(decision_package)

                        # Alternatives
                        ae = AlternativesEngine(runtime_provider=self.rp)
                        alternatives_package = ae.generate_all(anomaly_detector=ad)

                        # Approval — submit ke workflow
                        try:
                            from .approval import ApprovalWorkflow
                            aw = ApprovalWorkflow()
                            aw.submit_all(decision_package)
                            approval_pending = aw.get_pending().__len__()
                            approval_approved = aw.get_approved().__len__()
                            approval_rejected = aw.get_rejected().__len__()
                        except Exception:
                            pass
                except Exception:
                    pass

            # ============================================================
            # RCA — Root Cause Report (OP-72)
            # ============================================================
            root_cause_report = None
            if True:  # selalu evaluasi
                try:
                    from .rca import RootCauseAnalyzer
                    rca_analyzer = RootCauseAnalyzer(
                        runtime_provider=self.rp,
                        workspace_provider=(
                            getattr(self.rp, '_workspace_provider', None)
                            if self.rp else None
                        ),
                    )
                    ctx = {
                        "observed_event": sit_reason or "No specific event.",
                    }
                    q = "Why is {}?".format(sit_value.replace("_", " "))
                    rca_model = rca_analyzer.analyze(q, context=ctx)
                    rca_report = rca_analyzer.to_report(rca_model)
                    root_cause_report = {
                        "summary": rca_report.summary,
                        "root_cause": rca_report.root_cause,
                        "confidence": rca_report.confidence,
                        "supporting_evidence": rca_report.supporting_evidence,
                        "missing_observations": rca_report.missing_observations,
                    }
                except Exception:
                    root_cause_report = None

            # ============================================================
            # BUILD
            # ============================================================
            return ConversationObject(
                situation=sit_value,
                situation_summary=sit_label,
                situation_severity=severity,
                mission_target="Workspace",
                mission_condition=mission_condition,
                mission_activity=mission_activity,
                sam_action=sam_action,
                sam_decision="",
                sam_reason="",
                sam_confidence=0.0,
                facts=facts,
                evidence=evidence,
                user_action_needed=user_action,
                user_actions=user_actions,
                risks=risks,
                predictions=predictions_list,
                recommendations=recommendations_list,
                activity_changes=activity_changes,
                activity_count=len(stories),
                technical_details=tech,
                attention_label=att_label,
                attention_score=att_score,
                confidence=0.9 if severity == "information" else 0.8,
                root_cause=root_cause_report,
                decisions=decision_texts,
                decision_details=decision_package.to_dict() if decision_package else None,
                impact_details={
                    "assessments": [a.to_dict() for a in impact_package.assessments]
                } if impact_package else None,
                alternatives_details={
                    "alternatives": [a.to_dict() for a in alternatives_package.alternatives]
                } if alternatives_package else None,
                approval_pending_count=approval_pending,
                approval_approved_count=approval_approved,
                approval_rejected_count=approval_rejected,
            )

        except Exception as e:
            return ConversationObject(
                situation="error",
                situation_summary="Unable to understand the system.",
                situation_severity="critical",
                facts=["Error: {}".format(str(e))],
                user_action_needed="Check logs.",
                confidence=0.1,
            )

# Backward-compat alias
UnderstandingEngine = SystemAnalyzer


def _fmt_bytes(n: int) -> str:
    """Format bytes ke human-readable."""
    if n < 1024:
        return "{} B".format(n)
    elif n < 1024 * 1024:
        return "{:.1f} KB".format(n / 1024)
    elif n < 1024 * 1024 * 1024:
        return "{:.1f} MB".format(n / (1024 * 1024))
    else:
        return "{:.2f} GB".format(n / (1024 * 1024 * 1024))
