# Citizen Ecosystem - MISSION-3.3 (IP-3.3-001 Citizen Foundation
#                + IP-3.3-002 Citizen Collaboration & Compatibility
#                + IP-3.3-003 Citizen Certification & Ecosystem Intelligence)
#                + IP-3.4-001 Federation (dalam citizen/ sebagai bounded context)
# AO-3.3-001 / ED-3.3-001 + AO-3.4-001 / ED-3.4-001
#
# Bounded context citizen/: identity, registry, descriptor, capability,
# discovery, health, lifecycle, collaboration (models/proposal/compatibility/
# contract_resolution/dependency/explainability), ecosystem (certification/
# intelligence/health/recommendation/explainability), federation (identity/
# registry/discovery/descriptor/capability_exchange/health/api/compliance),
# api, compliance.
#
# Citizen adalah abstraksi konstitusional bersama: Runtime, Provider,
# Workflow, Mission, Policy, Capability semuanya JENIS (kind) citizen yang
# setara (Citizen Equality). Tidak ada entitas istimewa.
#
# Batas IP-3.3-001: identitas/registrasi/deskripsi/capability/lifecycle/
# discovery/compliance.
# Batas IP-3.3-002: kolaborasi & kompatibilitas antar-citizen (tanpa
# otoritas; collaboration != orchestration; proposal != decision).
# Batas IP-3.3-003: sertifikasi, evaluasi, pemahaman ekosistem (tanpa
# otoritas; certification != approval; intelligence != governance;
# recommendation != authority; ecosystem health != runtime control).
# Batas IP-3.4-001: Federation Foundation - mengakui & bertukar capability
# antar Citizen Ecosystem berdaulat (Federation != Distributed Runtime;
# registry metadata; capability exchange = advertisement; discovery =
# registry-based; health observasional; descriptor deklaratif; identity
# lokal dipertahankan; sovereignty first).

# re-expor API utama untuk konsumen platform
from sam.citizen.api.citizen import CitizenAPI, CitizenSummary
from sam.citizen.api.collaboration import (
    CitizenCollaborationAPI,
    CollaborationSummary,
)
from sam.citizen.api.intelligence import CitizenIntelligenceAPI
from sam.citizen.federation.api import FederationAPI
from sam.citizen.federation.interop_api import \
    FederationInteroperabilityAPI

__version__ = "3.4.0"

__all__ = ["CitizenAPI", "CitizenSummary",
           "CitizenCollaborationAPI", "CollaborationSummary",
           "CitizenIntelligenceAPI", "FederationAPI",
           "FederationInteroperabilityAPI"]
