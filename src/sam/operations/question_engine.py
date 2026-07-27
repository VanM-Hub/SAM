"""
Question Engine — Conversation-first Operations.

Question Engine adalah SATU-SATUNYA cara UI/CLI bertanya.

Alur baru:
ConversationObject
       ↓
QuestionIntent (pilih aspek)
       ↓
Renderer (DesktopRenderer)
       ↓
HumanAnswer (DTO presentasi)

TIDAK ada lagi Experience Contract.
TIDAK ada lagi builder paralel.
Semua dari ConversationObject.
"""

from typing import Optional

from .human_answer import HumanAnswer, DesktopRenderer
from .conversation_context import ConversationContext, InteractionMemory
from .conversation_context import ConversationContext, InteractionMemory
from .intent import QuestionIntent
from .intent_resolver import IntentResolver
from .understanding import UnderstandingEngine


class QuestionEngine:
    """Question Engine — render ConversationObject untuk intent tertentu.

    BUKAN NLP. BUKAN AI.
    Hanya memilih aspek ConversationObject yang relevan.
    """

    def __init__(self, experience_engine=None):
        self.understanding = UnderstandingEngine(experience_engine)
        self.renderer = DesktopRenderer()
        self.memory = InteractionMemory()

    def answer(self, question: str = "",
               context: Optional[ConversationContext] = None) -> HumanAnswer:
        """Jawab pertanyaan manusia.

        Pipeline:
        question → IntentResolver → Intent → ConversationObject → Renderer → HumanAnswer
        """
        # 1. Resolve intent
        intent = IntentResolver.resolve(question)

        # 2. Dapatkan konteks dari memori
        if context is None and self.memory:
            context = self.memory.get_context_for_followup(question)

        # 3. Dapatkan ConversationObject — SATU PANGGILAN
        co = self.understanding.understand()

        # 4. Render untuk intent ini
        answer = self.renderer.render(co, intent.value)

        # 5. Set metadata
        answer.question = question
        answer.intent = intent.value

        # 6. Simpan ke memori
        if self.memory:
            self.memory.update(question, intent, answer, context)

        return answer
