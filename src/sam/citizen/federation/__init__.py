# Federation - IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
# WP-01..10
#
# Layer: mengakui & bertukar capability antar beberapa Citizen Ecosystem yang
# berdaulat (sovereign) melalui contract. KEPUTUSAN ARSITEKTUR KUNCI:
# Federation != Distributed Runtime.
#
# Federation TIDAK berarti: remote execution, distributed scheduler,
# distributed runtime, global governance.
# Federation BERARTI: beberapa Citizen Ecosystem berdaulat saling MENGENALI
# dan BERTUKAR capability melalui contract (deskriptif, bukan eksekusi).
#
# Guardrail IP-3.4-001 dikunci (compliance.py FED-01..10):
#   Federation != Central Governance; Registry != Control Plane;
#   Capability Exchange != Execution; Discovery != Connection;
#   Health != Monitoring Control; Descriptor != Contract Execution;
#   Federation Identity != Global Identity; Sovereignty First.

# WP-01 - Federation Identity
from sam.citizen.federation.identity import (
    FederationIdentity,
    FederationMember,
    FederationInstance,
)

# WP-02 - Federation Registry
from sam.citizen.federation.registry import FederationRegistry

# WP-03 - Federation Discovery
from sam.citizen.federation.discovery import FederationDiscovery

# WP-04 - Federation Descriptor
from sam.citizen.federation.descriptor import (
    FederationDescriptor,
    build_federation_descriptor,
)

# WP-05 - Capability Exchange
from sam.citizen.federation.capability_exchange import (
    CapabilityAdvertisement,
    CapabilityExchange,
)

# WP-06 - Federation Health
from sam.citizen.federation.health import (
    FederationHealth,
    FederationHealthAssessor,
)

# WP-07 - Federation API
from sam.citizen.federation.api import FederationAPI

__all__ = [
    "FederationIdentity", "FederationMember", "FederationInstance",
    "FederationRegistry",
    "FederationDiscovery",
    "FederationDescriptor", "build_federation_descriptor",
    "CapabilityAdvertisement", "CapabilityExchange",
    "FederationHealth", "FederationHealthAssessor",
    "FederationAPI",
]
