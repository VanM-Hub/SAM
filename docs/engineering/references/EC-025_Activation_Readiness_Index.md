# EC-025 - Activation Readiness Index

Capability    Readiness    Tier    Activation Cost    Session
RuntimeService    100    Active    -    S01
ExecutionRuntime    100    Active    -    S01
Conversation    100    Active    -    S02
Provider    100    Active    -    S03
Presentation    100    Active    -    S04
Knowledge    100    Active    -    S05
Workflow    100    Active    -    S06
Artifact    85    Tier 1    LOW    S07 (Aktif)
Memory    70    Tier 1    LOW    S08 (Aktif)
Policy    85    Tier 1    LOW    S09 (Aktif) - S10 TDR selesai
Audit    85    Tier 1    LOW    S09 (Aktif) - S10 TDR selesai
Model    77    Tier 2    MEDIUM    Backlog*
Cognitive    70    Tier 1    LOW    Backlog
Skills    70    Tier 1    LOW    Backlog
Mission    60    Tier 2    MEDIUM    Backlog
Intelligence    40    Tier 3    HIGH    Architecture
Agent    42    Tier 3    HIGH    Architecture
Reasoning    35    Tier 3    HIGH    Architecture

Catatan:
- Nomor EC-025 dipakai krn EC-021 sdh ditempati "Architectural Heuristics" (R). EC ini
  berisi tabel saja (AD-ENG-001, RSR-A01).
- S10 diawali RSR. Jika Model Runtime tidak lagi memenuhi syarat (perubahan repo atau
  keputusan ADR/AD-ENG-001), S10 dialihkan menjadi Technical Debt Reduction tanpa
  mengubah urutan sesi sebelumnya.
- Capability bertanda "Architecture" = Backlog Architecture (bukan Engineering),
  karena activation model-nya belum memberi nilai operasional tanpa perubahan
  arsitektur (AD-ENG-001, RSR-I01).
