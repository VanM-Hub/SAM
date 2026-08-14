"""Environment-adaptive core SAM M14 (re-architecture).

Prinsip (instruksi Van 2026-08-14 17:45):
  - SAM harus environment-adaptive, TIDAK bergantung pada hardcoded
    application catalogue untuk discovery/investigation/diagnosis/recovery.
  - Alur: DISCOVERY -> IDENTIFICATION -> ENTRUSTMENT -> OBSERVATION
          -> INVESTIGATION -> DIAGNOSIS -> AUTHORITY -> EXECUTION -> VERIFICATION
  - Word/PDF/OpenClaw/Chrome dsb hanyalah CONTOH kelas masalah (fixture),
    BUKAN architectural dependency.
  - Acceptance berbasis "environment yang belum dikenal berhasil dipahami,
    diamati, didiagnosis, dan bila diizinkan diperbaiki" - bukan per-aplikasi.

Inti mesin generik:
  - entity.py      : model entitas + kind generik (process/port/service/file/...)
  - discovery.py   : enumerate environment secara generik (tanpa katalog)
  - graph.py       : bangun model/graph relasi antar-entitas
  - confidence.py  : ukur confidence berbasis evidence; jujur INSUFFICIENT
  - diagnosis.py   : pilih strategi investigation + root cause tanpa asumsi
                     jenis aplikasi; adaptif bila satu sumber gagal
  - remediation.py : pilih remediation berdasar capability yang tersedia,
                     lalu jalurkan lewat recovery canonical (bukan eksekusi
                     langsung)
  - providers.py   : CapabilityProvider/ProviderRegistry — instance capability
                     (Word/PDF/OpenClaw/GitHub/Provider) yang DIDAFTARKAN ke
                     mesin generic; TIDAK wajib, mesin jalan tanpa itu
  - capabilities.py: factory bungkus ward spesifik jadi provider instance

Alur lengkap tetap menjaga governance: eksekusi remediation HANYA lewat
canonical execution (ApprovalGate + AutonomousRecoveryLoop), belajar TANPA
memberi authority baru kepada SAM (lihat delegated_authority).
"""

from sam.environment.providers import (
    CapabilityProvider,
    ProviderObservation,
    ProviderRegistry,
    provider_from,
)

__all__ = [
    "CapabilityProvider",
    "ProviderObservation",
    "ProviderRegistry",
    "provider_from",
]
