# Compatibility shim for legacy CLI
__all__ = ["ExplainabilityEngine"]


class ExplainabilityEngine:
    """Minimal stubbed engine for legacy CLI imports."""

    def __init__(self, telemetry=None):
        self.telemetry = telemetry

    def explain(self, query: str) -> dict:
        return {"query": query, "explanation": f"Explanation for '{query}'", "confidence": 0.9}
