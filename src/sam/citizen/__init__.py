# Citizen Ecosystem - MISSION-3.3 (IP-3.3-001 Citizen Foundation)
# AO-3.3-001 / ED-3.3-001
#
# Bounded context citizen/: identity, registry, descriptor, capability,
# discovery, health, lifecycle, api, compliance.
#
# Citizen adalah abstraksi konstitusional bersama: Runtime, Provider,
# Workflow, Mission, Policy, Capability semuanya JENIS (kind) citizen yang
# setara (Citizen Equality). Tidak ada entitas istimewa.
#
# Batas IP-3.3-001: identitas/registrasi/deskripsi/capability/lifecycle/
# discovery/compliance. Belum kolaborasi antar-citizen (federation dll).

# re-expor API utama untuk konsumen platform
from sam.citizen.api.citizen import CitizenAPI, CitizenSummary

__version__ = "3.3.0"

__all__ = ["CitizenAPI", "CitizenSummary"]
