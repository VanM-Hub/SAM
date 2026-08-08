# Context Preservation - IP-3.5-001 (AO-ENG-001, MISSION-3.5)
# WP-04: menjaga konteks operasional tetap terjaga lintas navigasi.
#        Konteks = deskripsi keadaan tampilan, BUKAN keadaan runtime / otoritas.
#
# Bound context: src/sam/platform/ (consumer-only).
# Guardrail: Context != State Control; Preserve context != Lock state;
#   Konteks deklaratif != otoritas.

"""Context Preservation.

Menyimpan & memulihkan konteks tampilan (perspective aktif, domain terpilih,
region fokus) agar navigasi konsisten. Konteks ini milik layer penyajian
Platform Experience; bukan kontrol runtime dan bukan otoritas.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class WorkspaceContext:
    """Konteks tampilan workspace saat ini.

    Immutable. Memuat "di mana operator berada" di dalam tampilan.
    """

    perspective: str = "overview"
    # Domain yang sedang ditinjau (deklaratif).
    focus_domain: str = ""
    # Region yang sedang difokuskan (deklaratif).
    focus_region: str = ""
    # Path navigasi (stack deklaratif, FIFO dari index 0 = akar).
    breadcrumb: Tuple[str, ...] = ()

    def with_focus(self, domain: str = "", region: str = "") -> "WorkspaceContext":
        """Kembalikan konteks baru dengan focus yang diperbarui (immutable)."""
        return WorkspaceContext(
            perspective=self.perspective,
            focus_domain=domain or self.focus_domain,
            focus_region=region or self.focus_region,
            breadcrumb=self.breadcrumb,
        )

    def push_crumb(self, entry: str) -> "WorkspaceContext":
        """Dorong entri ke breadcrumb (immutable)."""
        return WorkspaceContext(
            perspective=self.perspective,
            focus_domain=self.focus_domain,
            focus_region=self.focus_region,
            breadcrumb=self.breadcrumb + (entry,),
        )

    def pop_crumb(self) -> "WorkspaceContext":
        """Keluarkan entri terakhir breadcrumb (immutable)."""
        if not self.breadcrumb:
            return self
        return WorkspaceContext(
            perspective=self.perspective,
            focus_domain=self.focus_domain,
            focus_region=self.focus_region,
            breadcrumb=self.breadcrumb[:-1],
        )

    def crumb_path(self) -> Tuple[str, ...]:
        """Path navigasi saat ini (deterministik)."""
        return tuple(self.breadcrumb)


class ContextStore:
    """Penyimpan konteks per-slot (deklaratif).

    Menyimpan konteks tampilan per identitas slot agar tetap terjaga lintas
    navigasi. Store ini tidak menahan akses/otoritas apa pun.
    """

    def __init__(self) -> None:
        self._store: Dict[str, WorkspaceContext] = {}

    def get(self, slot_id: str) -> WorkspaceContext:
        return self._store.get(slot_id, WorkspaceContext())

    def set(self, slot_id: str, context: WorkspaceContext) -> None:
        self._store[slot_id] = context

    def clear(self, slot_id: str) -> None:
        if slot_id in self._store:
            del self._store[slot_id]

    def keys(self) -> Tuple[str, ...]:
        return tuple(sorted(self._store.keys()))

    def __len__(self) -> int:
        return len(self._store)
