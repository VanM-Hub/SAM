"""
MissionSession — Sesi kerja pengguna.

SAM bukan chatbot tanya-jawab.
SAM adalah pendamping operasional.

MissionSession melacak:
- Sesi kerja: apa yang sedang dikerjakan pengguna
- Mission target: objek yang sedang diamati
- Timeline: aktivitas dalam sesi ini

Manusia bekerja dalam sesi. SAM harus mengerti sesi itu.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from .intent import QuestionIntent
from .audience import AudienceProfile, get_profile, AudienceType
from .human_answer import HumanAnswer


@dataclass
class MissionSession:
    """Sesi kerja — konteks operasional yang sedang dijalankan.

    Conversation bukan tanya-jawab.
    Conversation adalah pendampingan operasional.
    """
    # Sesi
    session_id: str = ""
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    current_page: str = "home"

    # Mission
    mission_target: str = "Workspace"
    mission_activity: str = ""          # "Deploy plugin v2", "Review approval"
    mission_progress: int = 0           # 0-100

    # Siapa yang berbicara
    audience: AudienceProfile = field(default_factory=lambda: get_profile(AudienceType.ADMINISTRATOR))

    # Riwayat percakapan dalam sesi ini
    last_question: str = ""
    last_intent: Optional[QuestionIntent] = None
    last_answer: Optional[HumanAnswer] = None
    question_count: int = 0
    context_hint: str = ""              # Petunjuk untuk pertanyaan berikutnya


class SessionManager:
    """Mengelola MissionSession.

    Sesi dimulai saat pengguna membuka SAM.
    Sesi berakhir saat pengguna tutup atau timeout.
    """

    def __init__(self):
        self._session = MissionSession()
        self._active = True

    @property
    def session(self) -> MissionSession:
        return self._session

    def start_session(self, audience_type: str = AudienceType.ADMINISTRATOR,
                      mission_target: str = "Workspace"):
        """Mulai sesi baru."""
        self._session = MissionSession(
            session_id="ses_{}".format(datetime.now().timestamp()),
            start_time=datetime.now().isoformat(),
            mission_target=mission_target,
            audience=get_profile(audience_type),
            question_count=0,
        )
        self._active = True

    def set_audience(self, audience_type: str):
        """Ganti audiens dalam sesi yang sama."""
        self._session.audience = get_profile(audience_type)

    def set_mission(self, target: str, activity: str = "", progress: int = 0):
        """Set mission target untuk sesi ini."""
        self._session.mission_target = target
        if activity:
            self._session.mission_activity = activity
        if progress:
            self._session.mission_progress = progress

    def set_context_hint(self, hint: str):
        """Petunjuk untuk pertanyaan berikutnya.

        Contoh: 'Deploy plugin v2.1 — Progress 42%'
        """
        self._session.context_hint = hint

    def record_interaction(self, question: str, intent: QuestionIntent,
                           answer: HumanAnswer):
        """Catat interaksi dalam sesi."""
        self._session.last_question = question
        self._session.last_intent = intent
        self._session.last_answer = answer
        self._session.question_count += 1

    def get_context_for_followup(self, question: str) -> str:
        """Dapatkan konteks untuk pertanyaan lanjutan.

        Jika 'Why?' setelah melihat deploy, SAM tahu konteksnya.
        """
        # Dari sesi kerja
        if self._session.context_hint:
            return self._session.context_hint

        # Dari pertanyaan terakhir
        if self._session.last_answer and self._session.last_answer.title:
            return self._session.last_answer.title[:80]

        # Dari mission
        if self._session.mission_activity:
            return self._session.mission_activity

        return ""

    def update_page(self, page: str):
        """Update halaman yang sedang dibuka."""
        self._session.current_page = page
