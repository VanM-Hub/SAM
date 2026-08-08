# Citizen Intelligence API - WP-27
# IP-3.3-003 (AO-3.3-001 / ED-3.3-001 cycle 3)
#
# Fasad read-only untuk Certification & Ecosystem Intelligence. Menjawab:
#   - Seberapa siap/patuh seorang Citizen?          -> certify / maturity
#   - Bagaimana kesehatan & keragaman ekosistem?    -> snapshot / health
#   - Apa rekomendasi peningkatan (advisory)?       -> recommend
#   - Mengapa hasilnya demikian?                    -> explain
#
# SELURUH metode read-only / advisory. Tidak ada certification-apply,
# no ecosystem control, no lifecycle mutation, no governance decision.

from typing import Dict, Optional, Sequence, Tuple

from sam.citizen.ecosystem.models import (
    CertificationResult,
    CitizenMaturityProfile,
)
from sam.citizen.ecosystem.certification_engine import CertificationEngine
from sam.citizen.ecosystem.intelligence import (
    EcosystemSnapshot,
    EcosystemIntelligenceEngine,
)
from sam.citizen.ecosystem.health import (
    EcosystemHealthAssessment,
    EcosystemHealthAssessor,
)
from sam.citizen.ecosystem.recommendation import (
    EcosystemRecommendation,
    EcosystemRecommendationEngine,
)
from sam.citizen.ecosystem.explainability import EcosystemExplainer


class CitizenIntelligenceAPI:
    """Fasad read-only / advisory Certification & Ecosystem Intelligence."""

    def __init__(self, registry=None, descriptors=None, healths=None):
        self._registry = registry
        self._descriptors = tuple(descriptors or ())
        self._healths = dict(healths or {})
        self._certifier = CertificationEngine(registry)
        self._intel = EcosystemIntelligenceEngine(registry)
        self._health_assessor = EcosystemHealthAssessor()
        self._recommender = EcosystemRecommendationEngine()
        self._explainer = EcosystemExplainer()

    # --- WP-22 - certification (read-only) ---

    def certify(self, identity_id: str,
                capabilities=None, contracts=None,
                health_status: str = "", lifecycle_stage: str = "",
                checks_passed=None, checks_total=None) -> CertificationResult:
        """Nilai readiness & compliance seorang Citizen (assessment)."""
        desc = self._descriptor(identity_id)
        return self._certifier.assess(
            identity_id, descriptor=desc,
            capabilities=capabilities, contracts=contracts,
            health_status=health_status, lifecycle_stage=lifecycle_stage,
            checks_passed=checks_passed, checks_total=checks_total)

    def maturity(self, identity_id: str,
                 capabilities=None, contracts=None,
                 health_status: str = "", lifecycle_stage: str = ""
                 ) -> CitizenMaturityProfile:
        desc = self._descriptor(identity_id)
        return self._certifier.profile(
            identity_id, descriptor=desc,
            capabilities=capabilities, contracts=contracts,
            health_status=health_status, lifecycle_stage=lifecycle_stage)

    # --- WP-23 - ecosystem intelligence (read-only) ---

    def snapshot(self, identity_ids: Sequence[str]) -> EcosystemSnapshot:
        kinds = {cid: self._kind(cid) for cid in identity_ids}
        healths = {cid: self._healths.get(cid, "unknown") for cid in identity_ids}
        caps = {cid: self._capabilities(cid) for cid in identity_ids}
        cts = {cid: self._contracts(cid) for cid in identity_ids}
        return self._intel.snapshot(
            identity_ids, kinds=kinds, healths=healths,
            capabilities=caps, contracts=cts)

    # --- WP-24 - ecosystem health (read-only) ---

    def health(self, identity_ids: Sequence[str]) -> EcosystemHealthAssessment:
        healths = {cid: self._healths.get(cid, "unknown") for cid in identity_ids}
        return self._health_assessor.assess(healths)

    # --- WP-25 - recommendation (advisory) ---

    def recommend(self, identity_ids: Sequence[str],
                  certifications: Dict[str, object] = None
                  ) -> Tuple[EcosystemRecommendation, ...]:
        health = self.health(identity_ids)
        snap = self.snapshot(identity_ids)
        return self._recommender.recommend(health, snap, certifications or {})

    # --- WP-26 - explainability (advisory) ---

    def explain_certification(self, cert) -> object:
        return self._explainer.explain_certification(cert)

    def explain_health(self, health) -> object:
        return self._explainer.explain_health(health)

    def explain_recommendation(self, rec) -> object:
        return self._explainer.explain_recommendation(rec)

    # --- helpers ---

    def _descriptor(self, identity_id):
        for d in self._descriptors:
            if getattr(d, "identity_id", None) == identity_id:
                return d
        return None

    def _kind(self, identity_id) -> str:
        if self._registry is not None:
            e = self._registry.get(identity_id)
            if e is not None:
                # RegistryEntry punya atribut .kind langsung
                k = getattr(e, "kind", None)
                if k:
                    return k
                ed = getattr(e, "as_dict", lambda: {})()
                ident = ed.get("identity") or {}
                return ident.get("kind", "unknown")
        d = self._descriptor(identity_id)
        if d is not None:
            return getattr(d, "kind", "unknown")
        return "unknown"

    def _capabilities(self, identity_id) -> Tuple[str, ...]:
        d = self._descriptor(identity_id)
        return tuple(getattr(d, "capabilities", ())) if d is not None else ()

    def _contracts(self, identity_id) -> Tuple[str, ...]:
        d = self._descriptor(identity_id)
        return tuple(getattr(d, "contracts", ())) if d is not None else ()
