"""
OP-43 — Architecture Review Gate

Lima pertanyaan wajib sebelum setiap merge besar.
"""

GATE = """
=====================================
ARCHITECTURE REVIEW GATE
=====================================

Sebelum merge, jawab:

[1] Apakah ini menambah KONSEP BARU?
    Jika ya, mengapa konsep lama tidak cukup?

[2] Apakah ini memperbesar PUBLIC API?
    Jika ya, apakah perlu dijamin stabil?
    (Public API hanya: SAM, Conversation, MissionSession)

[3] Apakah ini bisa diselesaikan dengan MEMPERKUAT
    komponen yang sudah ada?

[4] Apakah developer baru akan LEBIH MUDAH memahami
    SAM setelah perubahan ini?

[5] Jika saya menghapus komponen ini enam bulan lagi,
    SIAPA yang akan rusak?
    (Jawab 'banyak modul' = coupling masih terlalu tinggi)

=====================================
"""

def review():
    """Cetak gate."""
    print(GATE)
