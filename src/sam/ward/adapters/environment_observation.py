# Environment Observation Adapter - R1-002
#
# Adapter yang membuat implementation environment (EnvironmentDiscovery +
# EntityGraph) memenuhi kontrak observation (ward.capability.contracts.
# ObservationTarget / Observation) yang SUDAH dimiliki SAM.
#
# PENTING (semantic boundary, dikunci Van 2026-08-16):
#   - EnvironmentObservationAdapter BUKAN Ward baru.
#   - EnvironmentObservationAdapter TIDAK mendaftarkan komputer sebagai Citizen.
#   - Ia HANYA adapter yang menyesuaikan implementation environment ke port
#     observation yang sama dipakai Subject (Citizen|Ward).
#   - EnvironmentDiscovery tetap implementation generik; ia diobservasi
#     MELALUI adapter ini, bukan menjadi konsep baru.
#
# Read-only: TIDAK mengubah state eksternal, TIDAK membuat executor kedua,
# TIDAK import real_harness, TIDAK menyimpan authority.
from __future__ import annotations

from typing import Any, Dict, List

from sam.ward.capability.contracts import (
    Observation,
    ObservationTarget,
    SubjectRef,
)


class EnvironmentObservationAdapter(ObservationTarget):
    """ObservationTarget untuk environment mesin lokal (read-only).

    Membungkus EnvironmentDiscovery.discover() menjadi Observation dengan
    evidence + confidence dari observasi NYATA (probe process/port/file/env).

    `subject` adalah SubjectRef tujuan (mis. subject_id="local-machine",
    subject_type="citizen" atau bebas) — TAPI ini BUKAN pendaftaran Citizen;
    hanya untuk memberi konteks SubjectRef yang dibutuhkan kontrak Observation.

    Hasil:
      - payload : ringkasan discovery (entity_count, sources, failures).
      - evidence: entitas nyata + per-sumber confidence (bukan fixture).
      - successful: True bila minimal satu source menghasilkan entitas.
      - error   : deskripsi bila discovery gagal total; "" bila ada hasil.
    """

    def __init__(self, subject: SubjectRef,
                 discovery=None,
                 max_entities: int = 200) -> None:
        self._subject = subject
        # discovery diganti mudah utk test; default = mesin nyata.
        if discovery is None:
            from sam.environment.discovery import EnvironmentDiscovery
            discovery = EnvironmentDiscovery()
        self._discovery = discovery
        self._max_entities = max_entities

    def observe(self, *, capability: str = "observe") -> Observation:
        try:
            scan = self._discovery.discover()
        except Exception as exc:  # pragma: no cover - defensif
            # Gagal total -> BLOCKED jujur (0 side effect).
            return Observation(
                subject=self._subject,
                capability=capability,
                successful=False,
                payload={"error": str(exc), "entity_count": 0,
                         "sources": [], "failures": []},
                evidence={"verified_read": False, "entity_count": 0,
                          "sources": [], "failures": [], "total_failure": True},
                error="environment discovery gagal total: " + str(exc),
            )

        entities = list(getattr(scan, "entities", None) or [])
        # Bukti semua sumber nyata: cap PER SUMBER (bukan global) agar satu
        # sumber ramai (proses) tidak menenggelamkan sumber lain (port/file/env).
        per_source = self._max_entities
        entities = self._cap_per_source(entities, per_source)
        attrs = dict(getattr(scan, "attributes", None) or {})
        failures = list(attrs.get("failures") or [])
        failures = [{"source": f.get("source", ""), "error": f.get("error", "")}
                    for f in failures if isinstance(f, dict)]

        sources: List[str] = []
        for e in entities:
            s = e.source.value if hasattr(e.source, "value") else str(getattr(e, "source", ""))
            if s and s not in sources:
                sources.append(s)

        # evidence yang masuk ke state/audit: entitas nyata (provenance +
        # confidence), TIDAK mengambil attribute rahasia. `entities` sudah
        # di-cap per sumber; ambil sampel terwakili (mis. 20 per sumber).
        evidence_entities = [self._entity_summary(e) for e in self._cap_per_source(entities, 20)]

        ok = bool(entities)  # sukses bila setidaknya ada 1 entitas nyata
        return Observation(
            subject=self._subject,
            capability=capability,
            successful=ok,
            payload={
                "entity_count": len(entities),
                "sources": sources,
                "failures": failures,
                "entities_sample": evidence_entities,
            },
            evidence={
                "verified_read": ok,
                "entity_count": len(entities),
                "sources": sources,
                "failures": failures,
                "entities": evidence_entities,
                "timestamp": _utc_now(),
            },
            error="" if ok else "environment discovery tidak menghasilkan entitas (probe kosong/gagal)",
        )

    @staticmethod
    def _cap_per_source(entities: List, per_source: int) -> List:
        """Potong entitas per source (mekanisme discovery) agar SEMUA sumber
        terwakili di evidence, tidak hanya satu sumber ramai."""
        out: List = []
        count: Dict[str, int] = {}
        for e in entities:
            s = e.source.value if hasattr(e.source, "value") else str(getattr(e, "source", ""))
            if count.get(s, 0) >= per_source:
                continue
            count[s] = count.get(s, 0) + 1
            out.append(e)
        return out

    @staticmethod
    def _entity_summary(e) -> Dict[str, Any]:
        """Ringkasan entitas utk evidence UI/audit (tanpa attribute rahasia).

        `source` menunjukkan mekanisme discovery (process_table/port_table/
        file_table/env_table) — provenance, bukan asumsi aplikasi. `confidence`
        menunjukkan derajat keyakinan evidence.
        """
        kind = e.kind.value if hasattr(e.kind, "value") else str(getattr(e, "kind", ""))
        src = e.source.value if hasattr(e.source, "value") else str(getattr(e, "source", ""))
        label = str(getattr(e, "label", ""))
        attrs = dict(getattr(e, "attributes", None) or {})
        # ambil hanya beberapa atribut non-sensitif yang komunikatif
        keep_keys = ("pid", "status", "health", "path", "port", "address",
                     "env_key", "size_bytes", "valid_signature")
        safe_attrs = {k: attrs[k] for k in keep_keys if k in attrs}
        return {
            "id": str(getattr(e, "id", "")),
            "kind": kind,
            "source": src,
            "label": label,
            "attributes": safe_attrs,
            "confidence": getattr(e, "confidence", 1.0),
        }


def _utc_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
