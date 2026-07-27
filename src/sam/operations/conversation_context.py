"""
ConversationContext + InteractionMemory — OP-28/29.

Dipisah dari experience_contract agar QuestionEngine bisa independen.
"""

from dataclasses import dataclass, field
from typing import Optional

from .intent import QuestionIntent
from .human_answer import HumanAnswer


@dataclass
class ConversationContext:
    """Konteks percakapan — 'Why?' terhadap apa.

    QuestionEngine menerima question + context → jawaban kontekstual.
    """
    selected_work: str = ""
    selected_activity: str = ""
    selected_incident: str = ""
    selected_workspace: str = ""
    current_page: str = "home"
    last_intent: Optional[QuestionIntent] = None
    last_answer: Optional[str] = ""


@dataclass
class InteractionMemory:
    """Memori percakapan — membuat Why? terasa natural tanpa LLM."""
    last_question: str = ""
    last_intent: Optional[QuestionIntent] = None
    last_answer: Optional[HumanAnswer] = None
    last_context: Optional[ConversationContext] = None
    current_page: str = "home"

    def update(self, question: str, intent: QuestionIntent,
               answer: HumanAnswer, context: Optional[ConversationContext] = None):
        self.last_question = question
        self.last_intent = intent
        self.last_answer = answer
        if context:
            self.last_context = context

    def get_context_for_followup(self, question: str) -> ConversationContext:
        ctx = ConversationContext()
        if self.last_context:
            ctx.current_page = self.last_context.current_page
            ctx.selected_work = self.last_context.selected_work
            ctx.selected_activity = self.last_context.selected_activity
            ctx.selected_incident = self.last_context.selected_incident
            ctx.selected_workspace = self.last_context.selected_workspace
        return ctx
