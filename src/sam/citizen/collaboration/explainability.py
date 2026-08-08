# Collaboration Explainability - WP-16
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Menjelaskan alasan kolaborasi & kompatibilitas - mengapa dua citizen cocok,
# contract apa yang disatukan, apa basis penilaiannya. Explainability
# dipertahankan (semua output ber-alasan, evidence-backed).
#
# Murni eksplanasi, read-only.

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CollaborationExplanation:
    """Eksplanasi kolaborasi & kompatibilitas (immutable)."""

    subject: str
    statements: Tuple[str, ...] = ()
    evidence_items: Tuple[str, ...] = ()
    basis: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "subject": self.subject,
            "statements": list(self.statements),
            "evidence_items": list(self.evidence_items),
            "basis": list(self.basis),
        }


class CollaborationExplainer:
    """Membangun eksplanasi deterministik atas kolaborasi & kompatibilitas."""

    def explain_collaboration(self, spec, reason: str = "") -> CollaborationExplanation:
        """Jelaskan MENGAPA sebuah spesifikasi kolaborasi masuk akal."""
        statements = [
            "collaboration involves {} equal citizen(s)".format(len(spec.roles)),
            "roles are privilege-free: {}".format(
                ", ".join("{}:{}".format(r.role, r.citizen_identity_id)
                          for r in spec.roles)),
            "channel '{}' is {}".format(spec.channel.name,
                                        spec.channel.direction),
        ]
        if spec.shared_capabilities:
            statements.append("shared capabilities: {!s}".format(
                ", ".join(spec.shared_capabilities)))
        if reason:
            statements.append("reason: {}".format(reason))
        evidence = (
            "explicit roles in spec",
            "collaboration id {}".format(spec.collaboration_id),
            "privilege-free check: {} true".format(_privilege_free(spec)),
        )
        return CollaborationExplanation(
            subject="collaboration " + spec.collaboration_id,
            statements=tuple(statements),
            evidence_items=evidence,
            basis=("explainability preserved", "deterministic"),
        )

    def explain_compatibility(self, report) -> CollaborationExplanation:
        """Jelaskan MENGAPA dua citizen kompatibel / tidak."""
        if report.is_compatible:
            stmts = ("compatible: all checked capability/contract pairs match",
                     "{} contract(s) verified".format(len(report.entries)))
        else:
            failed = [e.contract for e in report.entries
                      if not e.verdict.compatible]
            stmts = ("NOT compatible: {} capability/contract mismatch".format(
                len(failed)),
                "mismatched: {!s}".format(", ".join(failed)))
        evidence = tuple(
            "{} = {!s}".format(e.contract, e.verdict.reasons)
            for e in report.entries)
        return CollaborationExplanation(
            subject="compatibility {} -> {}".format(
                report.source_identity_id, report.target_identity_id),
            statements=stmts,
            evidence_items=evidence,
            basis=("compatibility is assessment, not authority",
                   "deterministic"),
        )


def _privilege_free(spec) -> bool:
    from sam.citizen.collaboration.models import is_privilege_free
    return is_privilege_free(spec)
