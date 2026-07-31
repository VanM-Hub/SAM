"""Sprint 268 - Integration: integrasi read-only.

Menghubungkan pipeline akhir dengan Registry -> Graph -> Context secara
read-only. TIDAK mengubah subsystem lama dan TIDAK memanggil eksekusi.
"""
from __future__ import annotations

from typing import Tuple

from .intelligence_pipeline import IntelligencePipeline
from .intelligence_runtime import IntelligenceRuntime
from .runtime_session import RuntimeSession


class IntelligenceIntegration:
    """Integrasi read-only: jalankan pipeline intelligence untuk satu snapshot.

    Class service (bukan DTO); tidak menyimpan state mutabel.
    """

    def run(self, runtime: IntelligenceRuntime) -> RuntimeSession:
        # baca pipeline final (deskriptif) lalu jalankan intelligence
        return runtime.run()

    def pipeline_summary(self) -> Tuple[str, ...]:
        return IntelligencePipeline().stages
