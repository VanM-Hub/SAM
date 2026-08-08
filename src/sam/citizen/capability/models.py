# Citizen Capability Model - WP-04
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Capability-first modeling: citizen dimodelkan terutama dari KEMAMPUAN yang
# dimilikinya, bukan dari identitas fisiknya. Setiap capability:
#   - nama unik (capability_id)
#   - kontrak input/output (typed)
#   - deterministik (hasil bergantung hanya pada input)
#   - read-only di level registry: capability TIDAK dieksekusi di sini
#     (registry != authority / tidak menjalankan capability, ED-3.3-001).
#
# Murni model deskriptif capability.

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class CapabilityContract:
    """Kontrak sebuah capability (input/output typed)."""

    input_schema: str = ""     # deskripsi skema input (e.g. "any", "json.schema"..)
    output_schema: str = ""    # deskripsi skema output
    side_effects: Tuple[str, ...] = ()   # efek samping yang diizinkan (biasanya kosong)

    @property
    def is_read_only(self) -> bool:
        return len(self.side_effects) == 0

    def as_dict(self) -> Dict[str, object]:
        return {
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "side_effects": list(self.side_effects),
            "is_read_only": self.is_read_only,
        }


@dataclass(frozen=True)
class CitizenCapability:
    """Sebuah capability yang dimiliki seorang citizen (immutable)."""

    capability_id: str
    name: str
    contract: CapabilityContract = CapabilityContract()
    description: str = ""
    version: str = ""
    owner_identity_id: str = ""
    basis: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "capability_id": self.capability_id,
            "name": self.name,
            "contract": self.contract.as_dict(),
            "description": self.description,
            "version": self.version,
            "owner_identity_id": self.owner_identity_id,
            "basis": list(self.basis),
        }

    @classmethod
    def new(cls, name: str, *, owner_identity_id: str = "",
            input_schema: str = "", output_schema: str = "",
            side_effects: Tuple[str, ...] = (), description: str = "",
            version: str = "") -> "CitizenCapability":
        """Buat capability baru dengan id deterministik (sha1)."""
        canonical = "|".join([name.strip(), owner_identity_id,
                              input_schema, output_schema, version])
        digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]
        return cls(
            capability_id="cap-" + digest,
            name=name.strip(),
            contract=CapabilityContract(input_schema=input_schema,
                                        output_schema=output_schema,
                                        side_effects=side_effects),
            description=description.strip(),
            version=version.strip(),
            owner_identity_id=owner_identity_id,
            basis=("capability declared", "deterministic",
                   "read-only at registry level"),
        )
