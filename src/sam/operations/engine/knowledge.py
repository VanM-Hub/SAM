from typing import List, Dict, Any

class Insight:
    def __init__(self, title: str, severity: str = "info", description: str = ""):
        self.title = title
        self.severity = severity
        self.description = description


class Entry:
    def __init__(self, title: str, content: str, type: str = "knowledge"):
        self.title = title
        self.content = content
        self.type = type


class KnowledgeModel:
    def __init__(self, entries: List[Entry]):
        self.entries = entries
        self.total_entries = len(entries)
        # simple heuristics
        self.insights = [Insight(e.title, "info", e.content[:120]) for e in entries if "insight" in e.type.lower()]
        self.recommendation_count = len([e for e in entries if "recommend" in e.type.lower()])
        self.insight_count = len(self.insights)
        self.recommendations = [e for e in entries if "recommend" in e.type.lower()]


class KnowledgeEngine:
    """Compatibility KnowledgeEngine for legacy CLI/tests.

    Provides minimal in-memory knowledge store with deterministic content so
    legacy CLI code can run without the removed engine implementation.
    """

    def __init__(self, telemetry=None):
        self.telemetry = telemetry
        # seed with a few entries
        self._entries = [
            Entry("Default recommendation", "Run health-check on plugins.", type="recommendation"),
            Entry("Loaded knowledge", "Initial knowledge loaded.", type="knowledge"),
            Entry("Insight: spike", "Observed CPU spike in node A.", type="insight"),
        ]

    def get_knowledge(self) -> KnowledgeModel:
        return KnowledgeModel(self._entries)

    def search(self, query: str) -> List[Entry]:
        q = (query or "").lower()
        return [e for e in self._entries if q in e.title.lower() or q in e.content.lower()]

    def get_recommendations(self) -> List[Entry]:
        return [e for e in self._entries if e.type == "recommendation"]

    def add_entry(self, title: str, content: str, type: str = "knowledge") -> None:
        self._entries.append(Entry(title, content, type=type))
