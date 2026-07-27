"""
Question Engine — Conversation-first Operations.

Question Engine adalah SINGLE SOURCE untuk semua User-Facing Language.

TIDAK membaca string pertanyaan langsung.
Semua melalui QuestionIntent -> Experience Contract -> HumanAnswer.

Desktop, CLI, Assistant, Future Voice, Future API
-> semua lewat sini.
"""

from typing import Optional

from .human_answer import HumanAnswer
from .intent import QuestionIntent
from .intent_resolver import IntentResolver
from .experience_contract import (
    get_experience, ConversationContext, InteractionMemory,
)


class QuestionEngine:
    """Question Engine - Intent -> Experience -> Answer.

    BUKAN NLP.
    BUKAN AI.
    Ini adalah routing Intent ke Experience Contract.

    Question Engine hanya membaca:
    - IntentResolver (mengubah string -> Intent)
    - Experience Contract (setiap Intent punya Experience)
    - ConversationContext (konteks percakapan)
    - InteractionMemory (memori percakapan)
    """

    def __init__(self, experience_engine=None):
        self.ee = experience_engine
        self.memory = InteractionMemory()

    def answer(self, question: str = "",
               context: Optional[ConversationContext] = None) -> HumanAnswer:
        """Jawab pertanyaan manusia.

        Pipeline:
        question -> IntentResolver -> Intent -> Experience -> HumanAnswer
        """
        # 1. Resolve intent
        intent = IntentResolver.resolve(question)

        # 2. Dapatkan konteks dari memori jika tidak diberikan
        if context is None:
            context = self.memory.get_context_for_followup(question)

        # 3. Dapatkan Experience untuk intent ini
        experience = get_experience(intent, self.ee)

        # 4. Jawab
        answer = experience.answer(context)

        # 5. Set metadata
        answer.question = question
        answer.intent = intent.value

        # 6. Simpan ke memori
        self.memory.update(question, intent, answer, context)

        return answer
