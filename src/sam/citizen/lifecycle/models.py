# Citizen Lifecycle Model - WP-07
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Model lifecycle citizen - MURNI MODEL, bukan mutation.
# Registry/analyzer hanya MENYATAKAN tahap lifecycle, TIDAK men-trigger
# transisi. Transisi lifecycle tetap wewenang governance/authorized actor.
# (Registry != Authority, ED-3.3-001 Engineering Risks #2.)

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# tahap lifecycle yang dikenal (konsisten). Urutan kanonik:
#   declared -> registered -> discovered -> active -> retired
_LIFECYCLE_STAGES = ("declared", "registered", "discovered", "active", "retired")

# transisi yang diizinkan antar tahap (kanonik, deterministik).
_ALLOWED_TRANSITIONS = {
    "declared": ("registered",),
    "registered": ("discovered", "retired"),
    "discovered": ("active", "retired"),
    "active": ("retired",),
    "retired": (),
}


@dataclass(frozen=True)
class CitizenLifecycle:
    """Tahap lifecycle seorang citizen (immutable).

    stage     : salah satu dari _LIFECYCLE_STAGES
    history   : riwayat [('stage','timestamp')] (immutable tuple)
    basis     : alasan tahap ini (explainable)
    """

    identity_id: str
    stage: str = "declared"
    history: Tuple[Tuple[str, str], ...] = ()
    basis: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        st = self.stage.strip().lower()
        if st not in _LIFECYCLE_STAGES:
            st = "declared"
        object.__setattr__(self, "stage", st)

    def as_dict(self) -> Dict[str, object]:
        return {
            "identity_id": self.identity_id,
            "stage": self.stage,
            "history": list(self.history),
            "basis": list(self.basis),
        }


class CitizenLifecycleAnalyzer:
    """Menilai konsistensi tahap lifecycle & mengusulkan transisi (proposal).

    TIDAK pernah MENGUBAH lifecycle. Usulan transisi ditandai jelas `is_proposal`
    dan hanya berlaku bila dipicu authorized actor/governance.
    """

    def allowed_transitions_from(self, stage: str) -> Tuple[str, ...]:
        st = stage.strip().lower()
        if st not in _ALLOWED_TRANSITIONS:
            return ()
        return _ALLOWED_TRANSITIONS[st]

    def can_transition(self, current: str, target: str) -> bool:
        return target in self.allowed_transitions_from(current)

    def is_consistent(self, lifecycle: CitizenLifecycle) -> bool:
        """Lifecycle konsisten bila stage dikenal & urutan history valid."""
        if lifecycle.stage not in _LIFECYCLE_STAGES:
            return False
        prev = None
        for st, _ts in lifecycle.history:
            if st not in _LIFECYCLE_STAGES:
                return False
            if prev is not None and not self.can_transition(prev, st):
                return False
            prev = st
        return True

    def propose_transition(self, lifecycle: CitizenLifecycle,
                           target: str) -> Tuple[bool, str]:
        """USULKAN transisi ke `target` (proposal, tidak diterapkan).

        Mengembalikan (boleh, alasan). Penerapan tetap di luar scope.
        """
        if not self.can_transition(lifecycle.stage, target):
            return (False, "transition not allowed: {}".format(
                lifecycle.stage) + " -> " + target)
        return (True, "proposed transition (requires authorized actor): {}".format(
            lifecycle.stage) + " -> " + target)
