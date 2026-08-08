"""Audit Operational Intelligence - Workstream C5.

Observability mendalam terhadap Audit Runtime:
- C5.1 Evidence Explorer (integrasi dgn EvidenceExplorer existing)
- C5.2 Audit Timeline (descriptor audit terdaftar)
- C5.3 Audit Search (pencarian evidence/audit)
- C5.4 Audit Correlation (korelasi audit per kategori/sumber)
- C5.5 Compliance Status (status traceability/provenance)

READ-ONLY. Membaca data Audit yang sudah dipublikasikan runtime.
TIDAK merekam evidence baru, tidak mengubah audit trail.
Sesuai constraint AP-2C-001: observe, never govern.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# C5.2 Audit Timeline
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AuditView:
    """Satu audit yang diamati (immutable)."""
    audit_id: str = ""
    category: str = "general"
    description: str = ""
    provenance: bool = True
    traceability: bool = True
    tags: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "category": self.category,
            "description": self.description,
            "provenance": self.provenance,
            "traceability": self.traceability,
            "tags": list(self.tags),
        }


# ═══════════════════════════════════════════════════════════════════════
# C5.4 Audit Correlation
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AuditCorrelation:
    """Korelasi audit (immutable)."""
    total_audits: int = 0
    by_category: Tuple[Tuple[str, int], ...] = field(default_factory=tuple)
    traceable_count: int = 0
    provenance_count: int = 0

    def as_dict(self) -> dict:
        return {
            "total_audits": self.total_audits,
            "by_category": [{"category": k, "count": v} for k, v in self.by_category],
            "traceable_count": self.traceable_count,
            "provenance_count": self.provenance_count,
        }


# ═══════════════════════════════════════════════════════════════════════
# C5.5 Compliance Status
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ComplianceStatus:
    """Status kepatuhan audit (immutable)."""
    total_audits: int = 0
    traceable: int = 0
    provenance_ok: int = 0
    compliant: bool = True

    def as_dict(self) -> dict:
        return {
            "total_audits": self.total_audits,
            "traceable": self.traceable,
            "provenance_ok": self.provenance_ok,
            "compliant": self.compliant,
        }


# ═══════════════════════════════════════════════════════════════════════
# C5 report agregat
# ═══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class AuditIntelligenceReport:
    """Laporan intelligence audit (immutable)."""
    audits: Tuple[AuditView, ...] = field(default_factory=tuple)
    correlation: Optional[AuditCorrelation] = None
    compliance: Optional[ComplianceStatus] = None
    search_results: Tuple[AuditView, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "audit_count": len(self.audits),
            "audits": [a.as_dict() for a in self.audits],
            "correlation": self.correlation.as_dict() if self.correlation else None,
            "compliance": self.compliance.as_dict() if self.compliance else None,
            "search_results": [a.as_dict() for a in self.search_results],
        }


# ═══════════════════════════════════════════════════════════════════════
# C5 Observer
# ═══════════════════════════════════════════════════════════════════════

class AuditIntelligenceObserver:
    """Observer Audit - membaca publikasi audit (read-only).

    Menerima AuditRegistry opsional (di-inject dari wiring) agar dapat
    membaca descriptor yang SUDAH terdaftar. Observer TIDAK merekam.
    """

    def __init__(self, publication_registry=None, audit_registry=None) -> None:
        self._pub_registry = publication_registry
        self._audit_registry = audit_registry

    def audits(self) -> Tuple[AuditView, ...]:
        views: List[AuditView] = []
        if self._audit_registry is not None:
            try:
                for d in self._audit_registry.all_entries():
                    aid = getattr(d, "audit_id", getattr(d, "id", "unknown"))
                    views.append(AuditView(
                        audit_id=aid,
                        category=getattr(d, "category", "general"),
                        description=getattr(d, "description", ""),
                        provenance=bool(getattr(d, "provenance", True)),
                        traceability=bool(getattr(d, "traceability", True)),
                        tags=tuple(getattr(d, "tags", []) or []),
                    ))
            except Exception:
                pass
        else:
            pub = self._publication_for("audit")
            if pub and pub.dashboard_count > 0:
                views.append(AuditView(
                    audit_id="audit",
                    category="general",
                    description="Audit Runtime active",
                    provenance=True,
                    traceability=True,
                ))
        return tuple(views)

    # C5.2
    def timeline(self) -> Tuple[AuditView, ...]:
        return self.audits()

    # C5.4
    def correlation(self) -> AuditCorrelation:
        audits = self.audits()
        by_cat: dict = {}
        traceable = provenance = 0
        for a in audits:
            by_cat[a.category] = by_cat.get(a.category, 0) + 1
            if a.traceability:
                traceable += 1
            if a.provenance:
                provenance += 1
        order = sorted(by_cat.items(), key=lambda kv: (-kv[1], kv[0]))
        return AuditCorrelation(
            total_audits=len(audits),
            by_category=tuple(order),
            traceable_count=traceable,
            provenance_count=provenance,
        )

    # C5.5
    def compliance(self) -> ComplianceStatus:
        audits = self.audits()
        traceable = sum(1 for a in audits if a.traceability)
        provenance_ok = sum(1 for a in audits if a.provenance)
        compliant = all(a.traceability and a.provenance for a in audits)
        return ComplianceStatus(
            total_audits=len(audits),
            traceable=traceable,
            provenance_ok=provenance_ok,
            compliant=compliant,
        )

    # C5.3
    def search(self, query: str = "") -> Tuple[AuditView, ...]:
        """Cari audit berdasarkan kata kunci (read-only)."""
        q = (query or "").strip().lower()
        if not q:
            return ()
        return tuple(
            a for a in self.audits()
            if q in a.audit_id.lower()
            or q in a.category.lower()
            or q in a.description.lower()
            or any(q in t.lower() for t in a.tags)
        )

    # C5.1
    def evidence_summary(self):
        """Delegasi ke EvidenceExplorer existing (C-Phase 1)."""
        from sam.observation.evidence import EvidenceExplorer
        return EvidenceExplorer().index_all()

    def report(self, search_query: str = "") -> AuditIntelligenceReport:
        audits = self.audits()
        return AuditIntelligenceReport(
            audits=audits,
            correlation=self.correlation(),
            compliance=self.compliance(),
            search_results=self.search(search_query),
        )

    # ── helper ──
    def _publication_for(self, runtime_id: str):
        if self._pub_registry is None:
            return None
        try:
            for pub in self._pub_registry.observe_all().publications:
                if pub.runtime_id == runtime_id:
                    return pub
        except Exception:
            return None
        return None
