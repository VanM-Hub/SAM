"""
UnderstandingEngine — Sintesis ConversationObject dari semua sumber.

Input:
  Telemetry
  SituationEngine
  PresentationEngine
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


class UnderstandingEngine:
    """Sintesis ConversationObject — keadaan operasional yang dipahami manusia.

    BUKAN pembuat kalimat.
    BUKAN narator.
    Ini adalah otak yang memahami apa yang terjadi.
    """

    def __init__(self, experience_engine=None):
        self.ee = experience_engine

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
            # FACTS
            # ============================================================
            facts = []
            if sit:
                facts.append("Situation: {}.".format(sit_label))
                if sit_reason:
                    facts.append("Reason: {}.".format(sit_reason))
            if work_items:
                facts.append("Active work: {} item(s).".format(len(work_items)))

            # ============================================================
            # EVIDENCE
            # ============================================================
            evidence = []
            if sit and sit_reason:
                evidence.append(sit_reason)
            if not evidence:
                evidence.append("All systems operating normally.")

            # ============================================================
            # ACTIONS
            # ============================================================
            user_actions = []
            if user_action and "No action" not in user_action:
                user_actions.append(user_action)
            if recs:
                for r in recs[:2]:
                    if r.priority > 10:
                        user_actions.append(r.display())

            # ============================================================
            # RISKS + PREDICTIONS
            # ============================================================
            risks = []
            predictions_list = []
            for p in preds:
                if p.risk and p.risk != "None":
                    risks.append("{} — Risk: {}".format(p.event, p.risk))
                    predictions_list.append(p.display())

            # ============================================================
            # RECOMMENDATIONS
            # ============================================================
            recommendations_list = []
            for r in recs:
                if r.priority > 10:
                    recommendations_list.append(r.display())

            # ============================================================
            # ACTIVITY
            # ============================================================
            activity_changes = [s.title for s in stories[:5]]

            # ============================================================
            # TECHNICAL
            # ============================================================
            tech = pres.detail if pres else ""

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
