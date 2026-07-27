"""
Experience Contract — HumanExplainer Protocol + Registry.

Setelah OP-32, Experience classes (OverviewExperience, dll) sudah tidak ada.
Semua berasal dari ConversationObject.

HumanExplainer adalah kontrak untuk capability masa depan.
"""

from typing import Optional, Protocol

from .human_answer import HumanAnswer
from .conversation_context import ConversationContext


class HumanExplainer(Protocol):
    """Kontrak: setiap capability WAJIB mengimplementasikan ini.

    Capability tidak dianggap selesai sampai bisa:
    - Memberi overview
    - Menjelaskan kenapa terjadi
    - Merekomendasi langkah selanjutnya
    - Memprediksi konsekuensi
    """

    def overview(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        ...

    def explain(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        ...

    def next_step(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        ...

    def recommendation(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        ...

    def prediction(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        ...

    def technical(self, context: Optional[ConversationContext] = None) -> HumanAnswer:
        ...
