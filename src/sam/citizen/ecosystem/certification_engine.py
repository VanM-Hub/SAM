# Certification Engine - WP-22
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Evaluasi deterministik terhadap readiness & compliance Citizen. Menghitung
# maturity & compliance dari evidence/deskriptor yang tersedia, menghasilkan
# CertificationResult. Seluruhnya ASSESSMENT - tidak pernah mengubah status
# Citizen (Certification != Lifecycle Mutation; Certification != Approval).

from typing import Dict, Optional, Sequence, Tuple

from sam.citizen.ecosystem.models import CertificationResult, CitizenMaturityProfile


class CertificationEngine:
    """Menilai readiness & compliance Citizen (deterministik, read-only)."""

    # ambang maturity yang dianggap "layak" bila dipakai evaluator level
    DEFAULT_MATURITY_THRESHOLD = "capable"

    def __init__(self, registry=None):
        self._registry = registry

    def assess(self, identity_id: str, *,
               descriptor=None,
               health_status: str = "",
               capabilities: Optional[Sequence[str]] = None,
               contracts: Optional[Sequence[str]] = None,
               lifecycle_stage: str = "",
               checks_passed: Optional[int] = None,
               checks_total: Optional[int] = None) -> CertificationResult:
        """Nilai readiness & compliance seorang Citizen.

        Evidence diambil dari argument eksplisit (lebih prioritas), fallback
        ke descriptor/registry yang dipasang konstruktor.

        Output deterministik; input identik -> hasil identik.
        """
        caps = tuple(capabilities or ())
        contracts_ = tuple(contracts or ())
        if not caps and descriptor is not None:
            caps = tuple(getattr(descriptor, "capabilities", ()) or ())
        if not contracts_ and descriptor is not None:
            contracts_ = tuple(getattr(descriptor, "contracts", ()) or ())
        if health_status == "" and descriptor is not None:
            health_status = str(getattr(descriptor, "health_status", ""))
        if lifecycle_stage == "" and descriptor is not None:
            lifecycle_stage = str(getattr(descriptor, "lifecycle_stage", ""))

        # maturity: dari kepemilikan capability & lifecycle
        maturity = self._derive_maturity(
            has_capabilities=bool(caps),
            has_contracts=bool(contracts_),
            health=health_status,
            lifecycle=lifecycle_stage,
        )

        # compliance: proporsi cek yang ada tanda evidence
        if checks_total is None:
            checks_total = max(1, len(caps) + len(contracts_))
        if checks_passed is None:
            # deterministik: capability + contract = evidence inti
            checks_passed = min(checks_total, len(caps) + len(contracts_))
        ratio = (checks_passed / checks_total) if checks_total > 0 else 0.0
        if ratio >= 1.0:
            compliance = "compliant"
        elif ratio >= 0.5:
            compliance = "partial"
        else:
            compliance = "noncompliant"

        evidence = self._build_evidence(
            caps, contracts_, health_status, lifecycle_stage,
            checks_passed, checks_total)
        return CertificationResult.new(
            identity_id, maturity, compliance,
            int(checks_passed), int(checks_total),
            evidence=evidence,
            basis=("evaluation is deterministic",
                   "evidence-first",
                   "certification != approval"),
        )

    def profile(self, identity_id: str, *, descriptor=None,
                capabilities: Optional[Sequence[str]] = None,
                contracts: Optional[Sequence[str]] = None,
                health_status: str = "", lifecycle_stage: str = ""
                ) -> CitizenMaturityProfile:
        """Profil maturity ringkas seorang Citizen."""
        res = self.assess(identity_id, descriptor=descriptor,
                          capabilities=capabilities,
                          contracts=contracts,
                          health_status=health_status,
                          lifecycle_stage=lifecycle_stage)
        notes = (
            "maturity: {}".format(res.maturity),
            "compliance: {}".format(res.compliance),
        )
        return CitizenMaturityProfile(
            identity_id, res.maturity,
            assessed_at_basis=res.evidence,
            notes=notes,
        )

    # --- helpers ---

    def _derive_maturity(self, *, has_capabilities: bool,
                         has_contracts: bool, health: str,
                         lifecycle: str) -> str:
        if not has_capabilities and not has_contracts:
            return "initial"
        if not has_capabilities:
            return "defined"
        if lifecycle in ("active", "operational"):
            return "certified"
        if health in ("healthy",):
            return "capable"
        return "defined"

    def _build_evidence(self, caps: Tuple[str, ...],
                        contracts_: Tuple[str, ...], health: str,
                        lifecycle: str, passed: int, total: int) -> Tuple[str, ...]:
        ev = []
        if caps:
            ev.append("capabilities ({})".format(len(caps)))
        if contracts_:
            ev.append("contracts ({})".format(len(contracts_)))
        if health:
            ev.append("health status: {}".format(health))
        if lifecycle:
            ev.append("lifecycle stage: {}".format(lifecycle))
        ev.append("checks {}/{}".format(passed, total))
        return tuple(ev)
