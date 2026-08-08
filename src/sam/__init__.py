"""
SAM — Operating System for AI Operations.

PUBLIC API (frozen for v4):
  SAM           — Entry point. sam.observe() -> Conversation
  Conversation  — Semua interaksi. answer(), timeline(), dll.
  MissionSession— Konteks operasional sesi kerja.

@internal - Semua modul lain tidak dijamin stabil.
Berubah tanpa pemberitahuan.

Stability: STABLE_API
"""

__version__ = "2.0.0"

from .operations.conversation_api import Conversation
from .operations.conversation_api import SAM
from .operations.session import MissionSession

__all__ = ["SAM", "Conversation", "MissionSession"]
