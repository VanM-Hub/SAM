"""
OP-307 — Decision Conversation

Query conversation untuk decision.
Read-only — tidak memanggil penyedia langsung.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ConversationDecisionResponse:
    answer: str
    data: Optional[Dict[str, Any]] = None
    source: str = "decision"

    def to_dict(self) -> Dict[str, Any]:
        return {"answer": self.answer, "data": self.data, "source": self.source}


class DecisionConversation:
    """
    Query conversation untuk decision.
    Read-only — data berasal dari DecisionPackage yang sudah dibangun. Tidak memanggil penyedia layanan langsung.
    """

    def __init__(self, package: Any):
        self._package = package

    def explain_decision(self) -> ConversationDecisionResponse:
        """Jelaskan keputusan yang dipilih."""
        alt_name = self._get_selected_label()
        summary = getattr(self._package, "summary", "No summary available")
        score = getattr(self._package, "evaluation_score", 0.0)

        text = (
            f"Keputusan: {alt_name}\n\n"
            f"Ringkasan: {summary}\n\n"
            f"Skor evaluasi: {score}\n"
            f"Confidence: {getattr(self._package, 'estimated_confidence', 'N/A')}\n"
            f"Dampak: {getattr(self._package, 'estimated_impact', 'N/A')}"
        )
        return ConversationDecisionResponse(answer=text)

    def show_evidence(self) -> ConversationDecisionResponse:
        """Tampilkan evidence yang mendukung keputusan."""
        alternatives = getattr(self._package, "alternatives", ())
        selected_alt = getattr(self._package, "selected_alternative", "")

        selected = next(
            (a for a in alternatives if getattr(a, "name", "") == selected_alt),
            None,
        )
        if selected:
            eids = getattr(selected, "evidence_basis", ())
            text = (
                f"Evidence untuk {getattr(selected, 'label', selected_alt)}:\n"
                + "\n".join(f"  - {eid}" for eid in eids)
                if eids
                else "Tidak ada evidence spesifik"
            )
        else:
            text = getattr(self._package, "evidence_summary", "Tidak ada evidence")

        return ConversationDecisionResponse(answer=text)

    def show_alternatives(self) -> ConversationDecisionResponse:
        """Tampilkan semua alternatif."""
        alternatives = getattr(self._package, "alternatives", ())
        if not alternatives:
            return ConversationDecisionResponse(answer="Tidak ada alternatif")

        lines = ["**Alternatif:**"]
        for a in alternatives:
            name = getattr(a, "label", getattr(a, "name", "?"))
            desc = getattr(a, "description", "")
            risk = getattr(a, "risk_level", "?")
            conf = getattr(a, "estimated_confidence", "?")
            lines.append(f"- **{name}**: {desc[:80]} | Risiko: {risk} | Confidence: {conf}")

        return ConversationDecisionResponse(answer="\n".join(lines))

    def why_not(self, alternative: str = "") -> ConversationDecisionResponse:
        """Jelaskan mengapa alternatif tertentu tidak dipilih."""
        selected_alt = getattr(self._package, "selected_alternative", "").lower()

        if alternative and alternative.lower() == selected_alt:
            return ConversationDecisionResponse(
                answer=f"'{alternative}' adalah alternatif yang dipilih."
            )

        if not alternative:
            # Tampilkan semua alternatif yang tidak dipilih
            alternatives = getattr(self._package, "alternatives", ())
            lines = []
            for a in alternatives:
                name = getattr(a, "name", "")
                if name.lower() != selected_alt:
                    cons = getattr(a, "cons", ())
                    cons_text = "; ".join(cons[:3]) if cons else "Pertimbangan tidak tersedia"
                    lines.append(f"- **{getattr(a, 'label', name)}**: {cons_text}")
            return ConversationDecisionResponse(
                answer="Alternatif yang tidak dipilih:\n" + "\n".join(lines)
                if lines
                else "Tidak ada alternatif lain"
            )

        # Spesifik alternatif
        alternatives = getattr(self._package, "alternatives", ())
        for a in alternatives:
            if getattr(a, "name", "").lower() == alternative.lower():
                cons = getattr(a, "cons", ())
                risk = getattr(a, "risk_level", "?")
                text = (
                    f"Mengapa tidak memilih '{getattr(a, 'label', alternative)}':\n"
                    f"- Risiko: {risk}\n"
                    f"- Kekurangan: {'; '.join(cons[:3]) if cons else 'N/A'}"
                )
                return ConversationDecisionResponse(answer=text)

        return ConversationDecisionResponse(answer=f"Alternatif '{alternative}' tidak ditemukan.")

    def what_is_risk(self) -> ConversationDecisionResponse:
        """Tampilkan ringkasan risiko."""
        risk = getattr(self._package, "risk_summary", "Tidak ada data risiko")
        score = getattr(self._package, "evaluation_score", 0.0)
        text = (
            f"Ringkasan Risiko:\n{risk}\n\n"
            f"Dampak: {getattr(self._package, 'estimated_impact', 'N/A')}\n"
            f"Skor evaluasi: {score}\n"
            f"Confidence: {getattr(self._package, 'estimated_confidence', 'N/A')}"
        )
        return ConversationDecisionResponse(answer=text)

    def approval_needed(self) -> ConversationDecisionResponse:
        """Apakah keputusan ini butuh approval?"""
        needs = getattr(self._package, "requires_approval", False)
        alt = self._get_selected_label()
        if needs:
            return ConversationDecisionResponse(
                answer=f"Ya, alternatif '{alt}' memerlukan approval. "
                       "Approval request sudah disiapkan."
            )
        return ConversationDecisionResponse(
            answer=f"Tidak, alternatif '{alt}' tidak memerlukan approval."
        )

    def summarize(self) -> ConversationDecisionResponse:
        """Ringkasan lengkap."""
        text = (
            f"**Ringkasan Keputusan**\n\n"
            f"Pertanyaan: {getattr(self._package, 'operator_question', 'N/A')}\n"
            f"Keputusan: {self._get_selected_label()}\n"
            f"Confidence: {getattr(self._package, 'estimated_confidence', 'N/A')}\n"
            f"Dampak: {getattr(self._package, 'estimated_impact', 'N/A')}\n"
            f"Risiko: {getattr(self._package, 'risk_summary', 'N/A')}\n"
            f"Approval: {'Diperlukan' if getattr(self._package, 'requires_approval', False) else 'Tidak diperlukan'}\n"
            f"Skor: {getattr(self._package, 'evaluation_score', 'N/A')}\n\n"
            f"**Next Steps:**\n" + self._format_next_steps()
        )
        return ConversationDecisionResponse(answer=text)

    def next_step(self) -> ConversationDecisionResponse:
        """Langkah selanjutnya."""
        next_steps = getattr(self._package, "next_steps", ())
        if next_steps:
            lines = [f"{i+1}. {s}" for i, s in enumerate(next_steps)]
            return ConversationDecisionResponse(answer="**Next Steps:**\n" + "\n".join(lines))
        return ConversationDecisionResponse(answer="Tidak ada langkah selanjutnya.")

    def _get_selected_label(self) -> str:
        selected_alt = getattr(self._package, "selected_alternative", "")
        alternatives = getattr(self._package, "alternatives", ())
        selected = next(
            (a for a in alternatives if getattr(a, "name", "") == selected_alt),
            None,
        )
        return getattr(selected, "label", selected_alt) if selected else selected_alt

    def _format_next_steps(self) -> str:
        next_steps = getattr(self._package, "next_steps", ())
        if not next_steps:
            return "Tidak ada langkah selanjutnya."
        return "\n".join(f"  {i+1}. {s}" for i, s in enumerate(next_steps))
