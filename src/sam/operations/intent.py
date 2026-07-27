"""
QuestionIntent — Kontrak percakapan manusia.

BUKAN string.
BUKAN NLP.
Intent adalah jenis pertanyaan.

Semua UI mengirim Intent, bukan string mentah.
Desktop, CLI, API, Voice, semuanya Intent yang sama.
"""

from enum import Enum


class QuestionIntent(Enum):
    """Jenis pertanyaan — kontrak antara interface dan QuestionEngine.

    Setiap intent memiliki:
    - semantic_group: untuk fallback
    - priority: urutan pemrosesan
    """
    OVERVIEW = ("overview", "read", 10)
    HEALTH = ("health", "read", 20)
    USER_ACTION = ("user_action", "read", 30)
    EXPLAIN = ("explain", "reason", 40)
    CHANGES = ("changes", "history", 50)
    NEXT_STEP = ("next_step", "recommend", 60)
    CONSEQUENCE = ("consequence", "predict", 70)
    TECHNICAL = ("technical", "detail", 80)

    def __new__(cls, value, group, priority):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.group = group
        obj.priority = priority
        return obj
