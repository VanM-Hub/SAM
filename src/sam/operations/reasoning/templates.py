"""
OP-284 — Prompt Template Engine

Template immutable untuk berbagai jenis reasoning.
Semua template versioned.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


TEMPLATES: dict[str, str] = {
    "explain": (
        "Explain the following based on available evidence.\n"
        "---\n"
        "Question: {question}\n"
        "{conversation}"
        "{findings}"
        "{recommendations}"
        "---\n"
        "Provide a clear explanation with supporting citations."
    ),
    "recommend": (
        "Based on evidence, recommend the best course of action.\n"
        "---\n"
        "Question: {question}\n"
        "{findings}"
        "{recommendations}"
        "{mission}"
        "{health}"
        "---\n"
        "Provide actionable recommendations ranked by confidence."
    ),
    "compare": (
        "Compare the following options based on evidence.\n"
        "---\n"
        "Question: {question}\n"
        "{findings}"
        "{trust}"
        "---\n"
        "Provide a structured comparison."
    ),
    "summarize": (
        "Summarize the following information.\n"
        "---\n"
        "Question: {question}\n"
        "{conversation}"
        "{mission}"
        "{timeline}"
        "{observation}"
        "{health}"
        "---\n"
        "Provide a concise summary with key points."
    ),
    "investigate": (
        "Investigate the following based on evidence.\n"
        "---\n"
        "Question: {question}\n"
        "{findings}"
        "{timeline}"
        "{observation}"
        "{health}"
        "---\n"
        "Identify patterns, anomalies, and root causes."
    ),
    "health": (
        "Provide a health analysis based on the following data.\n"
        "---\n"
        "Question: {question}\n"
        "{health}"
        "{mission}"
        "{trust}"
        "---\n"
        "Evaluate system health, risks, and recommendations."
    ),
    "mission": (
        "Analyze mission status based on the following data.\n"
        "---\n"
        "Question: {question}\n"
        "{mission}"
        "{timeline}"
        "{findings}"
        "{health}"
        "---\n"
        "Provide mission status, blockers, and next steps."
    ),
    "timeline": (
        "Analyze timeline based on the following data.\n"
        "---\n"
        "Question: {question}\n"
        "{timeline}"
        "{mission}"
        "{observation}"
        "---\n"
        "Provide timeline analysis, key events, and trends."
    ),
}

TEMPLATE_VERSIONS: dict[str, str] = {}
for tname in TEMPLATES:
    TEMPLATE_VERSIONS[tname] = "1.0.0"
TEMPLATE_VERSIONS["_global_version"] = "1.0.0"


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    template: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "template": self.template,
        }


class TemplateEngine:
    """
    Prompt Template Engine.

    Memilih template berdasarkan nama.
    Semua template immutable — tidak bisa diubah runtime.
    """

    def get_template(self, name: str) -> PromptTemplate:
        if name not in TEMPLATES:
            raise ValueError(f"Unknown template: {name}. Available: {self.list_templates()}")
        return PromptTemplate(
            name=name,
            version=TEMPLATE_VERSIONS.get(name, "1.0.0"),
            template=TEMPLATES[name],
        )

    def list_templates(self) -> tuple[PromptTemplate, ...]:
        return tuple(
            PromptTemplate(name=n, version=TEMPLATE_VERSIONS.get(n, "1.0.0"),
                           template=TEMPLATES[n])
            for n in TEMPLATES
        )

    def render(self, name: str, context: dict[str, Any]) -> str:
        """Render template with context values."""
        tmpl = self.get_template(name)
        # Only substitute known placeholders
        result = tmpl.template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            if placeholder in result and value:
                result = result.replace(placeholder, f"\n{value}\n")
            else:
                result = result.replace(placeholder, "")
        return result

    def version(self, name: str = "") -> str:
        if not name:
            return TEMPLATE_VERSIONS["_global_version"]
        return TEMPLATE_VERSIONS.get(name, "1.0.0")
