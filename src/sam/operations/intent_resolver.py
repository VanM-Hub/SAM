"""
Intent Resolver — mengubah pertanyaan manusia menjadi QuestionIntent.

BUKAN NLP.
BUKAN AI.
Resolver hanya menggunakan keyword mapping deterministik.

Seluruh interface mengirim string → resolver → Intent.
"""

from .intent import QuestionIntent


class IntentResolver:
    """Mengubah string pertanyaan menjadi QuestionIntent.

    Mapping keyword-based, bukan semantic search.
    """

    # Mapping: keyword → intent
    INTENT_MAP = {
        # OVERVIEW
        "what's happening": QuestionIntent.OVERVIEW,
        "what is happening": QuestionIntent.OVERVIEW,
        "what's going on": QuestionIntent.OVERVIEW,
        "happening": QuestionIntent.OVERVIEW,
        "terjadi": QuestionIntent.OVERVIEW,
        "current status": QuestionIntent.OVERVIEW,
        "overview": QuestionIntent.OVERVIEW,
        "show me": QuestionIntent.OVERVIEW,
        "status": QuestionIntent.OVERVIEW,

        # HEALTH
        "is everything ok": QuestionIntent.HEALTH,
        "is everything okay": QuestionIntent.HEALTH,
        "are you ok": QuestionIntent.HEALTH,
        "everything ok": QuestionIntent.HEALTH,
        "everything okay": QuestionIntent.HEALTH,
        "healthy": QuestionIntent.HEALTH,
        "sehat": QuestionIntent.HEALTH,
        "baik": QuestionIntent.HEALTH,

        # USER_ACTION
        "do i need": QuestionIntent.USER_ACTION,
        "do anything": QuestionIntent.USER_ACTION,
        "what should i do": QuestionIntent.USER_ACTION,
        "any action": QuestionIntent.USER_ACTION,
        "action needed": QuestionIntent.USER_ACTION,
        "tindakan": QuestionIntent.USER_ACTION,
        "perlu": QuestionIntent.USER_ACTION,
        "approval": QuestionIntent.USER_ACTION,
        "waiting": QuestionIntent.USER_ACTION,

        # EXPLAIN
        "why": QuestionIntent.EXPLAIN,
        "kenapa": QuestionIntent.EXPLAIN,
        "mengapa": QuestionIntent.EXPLAIN,
        "explain": QuestionIntent.EXPLAIN,
        "jelaskan": QuestionIntent.EXPLAIN,
        "reason": QuestionIntent.EXPLAIN,
        "sebab": QuestionIntent.EXPLAIN,

        # CHANGES
        "what changed": QuestionIntent.CHANGES,
        "what changed?": QuestionIntent.CHANGES,
        "perubahan": QuestionIntent.CHANGES,
        "berubah": QuestionIntent.CHANGES,
        "recent": QuestionIntent.CHANGES,
        "history": QuestionIntent.CHANGES,

        # NEXT_STEP
        "should happen next": QuestionIntent.NEXT_STEP,
        "recommendation": QuestionIntent.NEXT_STEP,
        "next step": QuestionIntent.NEXT_STEP,
        "rekomendasi": QuestionIntent.NEXT_STEP,
        "selanjutnya": QuestionIntent.NEXT_STEP,
        "recommend": QuestionIntent.NEXT_STEP,
        "suggest": QuestionIntent.NEXT_STEP,

        # CONSEQUENCE
        "if i do nothing": QuestionIntent.CONSEQUENCE,
        "if i ignore": QuestionIntent.CONSEQUENCE,
        "what happens": QuestionIntent.CONSEQUENCE,
        "prediksi": QuestionIntent.CONSEQUENCE,
        "prediction": QuestionIntent.CONSEQUENCE,
        "nothing": QuestionIntent.CONSEQUENCE,
        "consequence": QuestionIntent.CONSEQUENCE,
        "risk": QuestionIntent.CONSEQUENCE,

        # TECHNICAL
        "technical": QuestionIntent.TECHNICAL,
        "detail": QuestionIntent.TECHNICAL,
        "teknis": QuestionIntent.TECHNICAL,
        "rinci": QuestionIntent.TECHNICAL,
        "show technical": QuestionIntent.TECHNICAL,
    }

    @classmethod
    def resolve(cls, question: str) -> QuestionIntent:
        """Ubah pertanyaan → Intent.

        Mencocokkan lowercase keyword.
        Fallback ke OVERVIEW jika tidak cocok.
        """
        if not question or not question.strip():
            return QuestionIntent.OVERVIEW

        q = question.lower().strip()

        # Coba exact match dulu
        if q in cls.INTENT_MAP:
            return cls.INTENT_MAP[q]

        # Coba partial match
        for keyword, intent in cls.INTENT_MAP.items():
            if keyword in q:
                return intent

        return QuestionIntent.OVERVIEW
