"""Resolution path state tracking.

Tracks the state of ADR-002 resolution as it progresses
through exact → compatible → tie-break path.

Authority: ADR-002 Decision
"""

from enum import Enum, auto


class ResolutionPathState(Enum):
    """Tracks resolution state through ADR-002 path.

    States:
        SEARCHING: Initial state — looking for matches.
        EXACT_FOUND: Exact identity+version match found.
        FALLBACK_SEARCHING: No exact match; searching compatible.
        FALLBACK_FOUND: Compatible match found.
        DEPRECATED_ONLY: Only deprecated candidates available.
        NOT_FOUND: No matching capabilities at all.
        VERSION_MISMATCH: Identity matches but version incompatible.
    """

    SEARCHING = auto()
    EXACT_FOUND = auto()
    FALLBACK_SEARCHING = auto()
    FALLBACK_FOUND = auto()
    DEPRECATED_ONLY = auto()
    NOT_FOUND = auto()
    VERSION_MISMATCH = auto()

    def is_terminal(self) -> bool:
        """Check if this is a terminal state.

        Returns:
            True for NOT_FOUND, VERSION_MISMATCH.
        """
        return self in (
            ResolutionPathState.NOT_FOUND,
            ResolutionPathState.VERSION_MISMATCH,
        )

    def has_result(self) -> bool:
        """Check if a capability was found.

        Returns:
            True for EXACT_FOUND, FALLBACK_FOUND, DEPRECATED_ONLY.
        """
        return self in (
            ResolutionPathState.EXACT_FOUND,
            ResolutionPathState.FALLBACK_FOUND,
            ResolutionPathState.DEPRECATED_ONLY,
        )
