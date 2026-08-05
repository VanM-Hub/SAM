"""Audit Recording Helper — Composition Root Holder (L6, pendekatan C).

Peran: menyediakan titik baca registry Audit terbaru di Composition Root/Entry,
agar record audit terminal dari outcome preview dapat dilihat TANPA:
- mengubah AuditRegistry (tetap immutable),
- mengubah AuditPreviewConsumer,
- mengubah execution_runtime / activation flow,
- mengubah ownership / lifecycle / Runtime Model.

Pola:
    AuditRegistryRef (holder) di Composition Root/Entry
      ├─ .get()   -> registry terbaru (titik baca)
      ├─ .set(r)  -> swap referensi ke instance hasil register (registry immutable)
      └─ .record_from_outcome(outcome) -> catat 1 record terminal dari outcome preview

Audit tetap terminal observer; tidak ada feedback; tidak ada dependency Execution→Audit
(holder dipanggil dari wiring entry, bukan dari execution_runtime).
"""
from __future__ import annotations

from sam.audit_runtime.foundation.audit_registry import AuditRegistry
from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor
from .preview_gateway import PreviewOutcomeView


class AuditRegistryRef:
    """Holder referensi ke AuditRegistry (registry immutable; hanya referensi di-swap).

    Digunakan di Composition Root/Entry sebagai titik baca registry audit terbaru.
    """

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry

    def get(self) -> AuditRegistry:
        """Registry audit terbaru (titik baca)."""
        return self._registry

    def set(self, registry: AuditRegistry) -> None:
        """Perbarui referensi ke instance hasil register (objek lama tak dimutasi)."""
        self._registry = registry

    def count(self) -> int:
        return self._registry.count()

    def record_from_outcome(
        self,
        outcome: PreviewOutcomeView,
        category: str = "execution.preview",
    ) -> None:
        """Catat satu record audit terminal dari outcome preview.

        Membangun AuditDescriptor lalu register; karena registry immutable,
        referensi holder di-swap ke instance hasil register.
        Audit = terminal observer: tidak mempengaruhi outcome; tidak melempar
        pada kegagalan (tidak memutus flow pemanggil).
        """
        audit_id = "audit-%s" % (outcome.runtime_id or "preview")
        descriptor = AuditDescriptor(
            audit_id=audit_id,
            category=category,
            description=(
                "preview outcome: approved=%s executed=%s external_calls=%s status=%s"
                % (outcome.approved, outcome.executed, outcome.external_calls, outcome.status)
            ),
            provenance=True,
            traceability=True,
            tags=["preview", outcome.mode],
        )
        try:
            self.set(self._registry.register(descriptor))
        except Exception:  # pragma: no cover - guard; audit tidak boleh memutus flow
            pass
