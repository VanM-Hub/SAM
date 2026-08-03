"""Entry point for `python -m sam.runtime_root` (E1-002 CLI).

Executes the deterministic smoke sequence:
    build -> start -> health -> stop -> dispose.

Authority: E1-002 REFERENCE RUNTIME EXECUTABLE.
"""

from .main import _main

if __name__ == "__main__":
    import sys

    from .exceptions import RuntimeCompositionError

    try:
        sys.exit(_main())
    except RuntimeCompositionError as exc:
        print("sam.runtime_root: ERROR: %s" % exc, file=sys.stderr)
        sys.exit(3)
