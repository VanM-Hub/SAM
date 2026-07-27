"""
InteractionIntent — Semua bentuk interaksi manusia.

Bukan cuma pertanyaan teks.
Click, Voice, Notification, API, Automation — semuanya interaksi.
"""

from enum import Enum


class InteractionIntent(Enum):
    """Jenis interaksi — menggantikan QuestionIntent.

    Intent tidak lagi diasumsikan dari pertanyaan teks.
    Intent berasal dari semua bentuk interaksi.
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
