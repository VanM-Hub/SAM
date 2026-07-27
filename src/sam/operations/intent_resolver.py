"""
Intent Resolver — mengubah pertanyaan manusia menjadi InteractionIntent.

BUKAN NLP.
BUKAN AI.
Resolver hanya menggunakan keyword mapping deterministik.

Seluruh interface mengirim string → resolver → Intent.
"""

from .intent import InteractionIntent


class IntentResolver:
    """Mengubah string pertanyaan menjadi InteractionIntent.

    Mapping keyword-based, bukan semantic search.
    """

    # Mapping: keyword → intent
    INTENT_MAP = {
        # OVERVIEW
        "what's happening": InteractionIntent.OVERVIEW,
        "what is happening": InteractionIntent.OVERVIEW,
        "what's going on": InteractionIntent.OVERVIEW,
        "happening": InteractionIntent.OVERVIEW,
        "terjadi": InteractionIntent.OVERVIEW,
        "current status": InteractionIntent.OVERVIEW,
        "overview": InteractionIntent.OVERVIEW,
        "show me": InteractionIntent.OVERVIEW,
        "status": InteractionIntent.OVERVIEW,

        # HEALTH
        "is everything ok": InteractionIntent.HEALTH,
        "is everything okay": InteractionIntent.HEALTH,
        "are you ok": InteractionIntent.HEALTH,
        "everything ok": InteractionIntent.HEALTH,
        "everything okay": InteractionIntent.HEALTH,
        "healthy": InteractionIntent.HEALTH,
        "sehat": InteractionIntent.HEALTH,
        "baik": InteractionIntent.HEALTH,

        # USER_ACTION
        "do i need": InteractionIntent.USER_ACTION,
        "do anything": InteractionIntent.USER_ACTION,
        "what should i do": InteractionIntent.USER_ACTION,
        "any action": InteractionIntent.USER_ACTION,
        "action needed": InteractionIntent.USER_ACTION,
        "tindakan": InteractionIntent.USER_ACTION,
        "perlu": InteractionIntent.USER_ACTION,
        "approval": InteractionIntent.USER_ACTION,
        "waiting": InteractionIntent.USER_ACTION,

        # EXPLAIN
        "why": InteractionIntent.EXPLAIN,
        "kenapa": InteractionIntent.EXPLAIN,
        "mengapa": InteractionIntent.EXPLAIN,
        "explain": InteractionIntent.EXPLAIN,
        "jelaskan": InteractionIntent.EXPLAIN,
        "reason": InteractionIntent.EXPLAIN,
        "sebab": InteractionIntent.EXPLAIN,

        # CHANGES
        "what changed": InteractionIntent.CHANGES,
        "what changed?": InteractionIntent.CHANGES,
        "perubahan": InteractionIntent.CHANGES,
        "berubah": InteractionIntent.CHANGES,
        "recent": InteractionIntent.CHANGES,
        "history": InteractionIntent.CHANGES,

        # NEXT_STEP
        "should happen next": InteractionIntent.NEXT_STEP,
        "recommendation": InteractionIntent.NEXT_STEP,
        "next step": InteractionIntent.NEXT_STEP,
        "rekomendasi": InteractionIntent.NEXT_STEP,
        "selanjutnya": InteractionIntent.NEXT_STEP,
        "recommend": InteractionIntent.NEXT_STEP,
        "suggest": InteractionIntent.NEXT_STEP,

        # CONSEQUENCE
        "if i do nothing": InteractionIntent.CONSEQUENCE,
        "if i ignore": InteractionIntent.CONSEQUENCE,
        "what happens": InteractionIntent.CONSEQUENCE,
        "prediksi": InteractionIntent.CONSEQUENCE,
        "prediction": InteractionIntent.CONSEQUENCE,
        "nothing": InteractionIntent.CONSEQUENCE,
        "consequence": InteractionIntent.CONSEQUENCE,
        "risk": InteractionIntent.CONSEQUENCE,

        # TECHNICAL
        "technical": InteractionIntent.TECHNICAL,
        "detail": InteractionIntent.TECHNICAL,
        "teknis": InteractionIntent.TECHNICAL,
        "rinci": InteractionIntent.TECHNICAL,
        "show technical": InteractionIntent.TECHNICAL,
    }

    @classmethod
    def resolve(cls, question: str) -> InteractionIntent:
        """Ubah pertanyaan → Intent.

        Mencocokkan lowercase keyword.
        Fallback ke OVERVIEW jika tidak cocok.
        """
        if not question or not question.strip():
            return InteractionIntent.OVERVIEW

        q = question.lower().strip()

        # Coba exact match dulu
        if q in cls.INTENT_MAP:
            return cls.INTENT_MAP[q]

        # Coba partial match
        for keyword, intent in cls.INTENT_MAP.items():
            if keyword in q:
                return intent

        return InteractionIntent.OVERVIEW
