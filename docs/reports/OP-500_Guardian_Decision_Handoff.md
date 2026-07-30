# OP-500: Guardian Decision Handoff — Dokumentasi Sprint 49

Menghubungkan Guardian Operational Intent ke Decision Runtime via DecisionInput DTO.

**v5.6.0**

7 file baru: decision_input.py, handoff.py, mapping.py, eligibility.py, queue.py, conversation_handoff.py, dashboard_handoff.py

Pipeline: Event → Dispatch → Sync → Transitions → Situations → Assessment → Intent → **Decision Handoff** → Reasoning → Learning → Preview → Dashboard → Conversation

Tidak memanggil Decision Runtime. Tidak membuat mission. Tidak submit approval.
