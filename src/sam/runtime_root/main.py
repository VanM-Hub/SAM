"""Reference Runtime Executable (E1-002).

Makes the composed Reference Runtime runnable:

    * create_runtime()   -- build a fresh RuntimeRoot (BUILT).
    * run_runtime()      -- build + start + report aggregate health.
    * shutdown_runtime() -- stop + dispose (terminal DISPOSED).

CLI (E1-002):
    python -m sam.runtime_root

Executes the deterministic smoke sequence:
    build -> start -> health -> stop -> dispose

No network, no timestamps, no random output — deterministic stdout only, so it
is safe to run headless and offline.

Authority: E1-002 REFERENCE RUNTIME EXECUTABLE | E1-001 COMPOSITION ROOT
            | R5-001 | I1-001 | I0-001
"""

from __future__ import annotations

from typing import Optional

from .exceptions import RuntimeCompositionError
from .health import HealthStatus
from .lifecycle import RuntimeState
from .runtime_builder import PIPELINE, RuntimeBuilder
from .runtime_root import RuntimeRoot


def create_runtime() -> RuntimeRoot:
    """Build a fresh Reference Runtime (does not start it).

    Returns:
        A RuntimeRoot in BUILT state.
    """
    return RuntimeBuilder().build()


def run_runtime() -> RuntimeRoot:
    """Build and start the Reference Runtime, then report aggregate health.

    Returns:
        The running RuntimeRoot (STARTED state).
    """
    root = create_runtime()
    root.start()
    return root


def shutdown_runtime(root: RuntimeRoot) -> None:
    """Stop and dispose the runtime deterministically.

    Args:
        root: the root returned by create_runtime/run_runtime/start.

    Raises:
        RuntimeCompositionError: if the runtime cannot be shut down (e.g.
        already disposed).
    """
    if root.lifecycle.state in (RuntimeState.STARTED, RuntimeState.BUILT):
        root.stop()
    if root.lifecycle.state == RuntimeState.DISPOSED:
        raise RuntimeCompositionError(
            "Runtime is already disposed"
        )
    if root.lifecycle.state != RuntimeState.STOPPED:
        raise RuntimeCompositionError(
            "Cannot shut down runtime in state: %s" % root.lifecycle.state.value
        )
    root.dispose()


def _main() -> int:
    """CLI entry point: build -> start -> health -> stop -> dispose."""
    builder = RuntimeBuilder()
    root = builder.build()
    print("sam.runtime_root: built (state=%s)" % root.lifecycle.state.value)
    root.start()
    print("sam.runtime_root: started (state=%s)" % root.lifecycle.state.value)
    health = root.health()
    print(
        "sam.runtime_root: health=%s (units=%d, pipeline=%d)"
        % (health.value, len(root.container()), len(PIPELINE))
    )
    root.stop()
    print("sam.runtime_root: stopped (state=%s)" % root.lifecycle.state.value)
    root.dispose()
    print("sam.runtime_root: disposed (state=%s)" % root.lifecycle.state.value)
    return 0


if __name__ == "__main__":
    import sys

    try:
        sys.exit(_main())
    except RuntimeCompositionError as exc:
        print("sam.runtime_root: ERROR: %s" % exc, file=sys.stderr)
        sys.exit(3)
