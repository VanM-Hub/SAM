"""
CLI Renderer — HumanAnswer → teks terminal.
"""

from ..operations.human_answer import HumanAnswer


class CLIRenderer:
    """Render HumanAnswer untuk CLI/terminal."""

    def render(self, answer: HumanAnswer) -> str:
        parts = []
        if answer.title:
            parts.append(answer.title)
        if answer.summary and answer.summary != answer.title:
            parts.append(answer.summary)

        # Sections
        for heading, content in answer.sections:
            parts.append("")
            parts.append("-- {} --".format(heading))
            parts.append(content)

        # Cards
        for icon, title, detail in answer.cards:
            parts.append("")
            parts.append("{} {} — {}".format(icon, title, detail[:60]))

        # Actions
        if answer.actions:
            parts.append("")
            for a in answer.actions:
                parts.append("  [{}]".format(a))

        # Details (backward compat)
        if answer.details:
            parts.append("")
            parts.append(answer.details)

        return "\n".join(parts)

    def render_short(self, answer: HumanAnswer) -> str:
        """Render pendek untuk notifikasi."""
        parts = [answer.title]
        if answer.actions:
            parts.append("Action: {}".format(answer.actions[0]))
        return " -- ".join(parts)
