# Citizen Ecosystem - MISSION-3.3 (IP-3.3-001 Citizen Foundation + IP-3.3-002
# Citizen Collaboration & Compatibility)
# AO-3.3-001 / ED-3.3-001
#
# Bounded context citizen/: identity, registry, descriptor, capability,
# discovery, health, lifecycle, collaboration (models/proposal/compatibility/
# contract_resolution/dependency/explainability), api, compliance.
#
# Citizen adalah abstraksi konstitusional bersama: Runtime, Provider,
# Workflow, Mission, Policy, Capability semuanya JENIS (kind) citizen yang
# setara (Citizen Equality). Tidak ada entitas istimewa.
#
# Batas IP-3.3-001: identitas/registrasi/deskripsi/capability/lifecycle/
# discovery/compliance.
# Batas IP-3.3-002: kolaborasi & kompatibilitas antar-citizen (tanpa
# otoritas; collaboration != orchestration; proposal != decision).

# re-expor API utama untuk konsumen platform
from sam.citizen.api.citizen import CitizenAPI, CitizenSummary
from sam.citizen.api.collaboration import (
    CitizenCollaborationAPI,
    CollaborationSummary,
)

__version__ = "3.3.0"

__all__ = ["CitizenAPI", "CitizenSummary",
           "CitizenCollaborationAPI", "CollaborationSummary"]
