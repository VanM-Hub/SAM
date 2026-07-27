"""
Desktop Widget Renderer — HumanAnswer → widget info.
"""

from ..operations.human_answer import HumanAnswer


class DesktopRenderer:
    """Render HumanAnswer untuk logika widget Desktop.

    Output: dict dengan field semantik untuk PySide6 widgets.
    BUKAN string. BUKAN widget langsung.
    """

    def render(self, answer: HumanAnswer) -> dict:
        data = {
            "title": answer.title,
            "summary": answer.summary,
            "severity": answer.severity,
            "priority": answer.priority,
            "icon": answer.icon or self._icon_for_severity(answer.severity),
            "sections": [],
        }

        for heading, content in answer.sections:
            data["sections"].append({"heading": heading, "content": content})

        # Cards
        for icon, title, detail in answer.cards:
            data.setdefault("cards", []).append({
                "icon": icon, "title": title, "detail": detail,
            })

        # Badges
        for text, color in answer.badges:
            data.setdefault("badges", []).append({"text": text, "color": color})

        # Actions
        if answer.actions:
            data["actions"] = list(answer.actions)

        return data

    def _icon_for_severity(self, severity: str) -> str:
        icons = {
            "info": "\u2139\ufe0f",
            "success": "\u2705",
            "warning": "\u26a0\ufe0f",
            "error": "\u274c",
            "critical": "\U0001f6a8",
        }
        return icons.get(severity, "\u2139\ufe0f")
