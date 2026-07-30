"""Activation Rules — aturan dasar aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivationRule:
    name: str = ""
    description: str = ""
    applies_to: str = "all"
    priority: int = 0


class ActivationRules:
    """Rule engine untuk aktivasi — rule-based."""

    DEFAULT_RULES = {
        "no_empty_draft": ActivationRule(
            "no_empty_draft", "Draft tidak boleh kosong", "all", 10
        ),
        "confidence_min_0_1": ActivationRule(
            "confidence_min_0_1", "Min confidence 0.1", "candidate", 20
        ),
        "priority_positive": ActivationRule(
            "priority_positive", "Priority score >= 0", "candidate", 30
        ),
        "candidate_type_valid": ActivationRule(
            "candidate_type_valid", "Tipe kandidat harus dikenal", "candidate", 40
        ),
        "context_exists": ActivationRule(
            "context_exists", "ActivationContext harus ada", "draft", 50
        ),
        "candidate_exists": ActivationRule(
            "candidate_exists", "Min 1 kandidat per draft", "draft", 60
        ),
    }

    def list_rules(self) -> List[ActivationRule]:
        return list(self.DEFAULT_RULES.values())

    def list_by_scope(self, scope: str) -> List[ActivationRule]:
        return [r for r in self.DEFAULT_RULES.values() if r.applies_to == scope or r.applies_to == "all"]

    def all_scopes(self) -> List[str]:
        rv: List[str] = []
        for r in self.DEFAULT_RULES.values():
            if r.applies_to not in rv:
                rv.append(r.applies_to)
        return rv

    def get_rule(self, name: str) -> Optional[ActivationRule]:
        return self.DEFAULT_RULES.get(name)
