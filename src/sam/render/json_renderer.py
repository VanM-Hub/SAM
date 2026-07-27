"""
JSON Renderer — HumanAnswer → JSON.
"""

import json

from ..operations.human_answer import HumanAnswer


class JSONRenderer:
    """Render HumanAnswer untuk API."""

    def render(self, answer: HumanAnswer) -> dict:
        return {
            "question": answer.question,
            "title": answer.title,
            "summary": answer.summary,
            "details": answer.details,
            "sections": [
                {"heading": h, "content": c}
                for h, c in answer.sections
            ],
            "cards": [
                {"icon": ic, "title": t, "detail": d}
                for ic, t, d in answer.cards
            ],
            "actions": list(answer.actions),
            "severity": answer.severity,
            "priority": answer.priority,
            "icon": answer.icon,
            "badges": [
                {"text": t, "color": c}
                for t, c in answer.badges
            ],
            "intent": answer.intent,
        }
