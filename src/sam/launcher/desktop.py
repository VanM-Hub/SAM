"""
Desktop Launcher — entry module untuk SAM desktop.

Dirujuk oleh Dockerfile ENTRYPOINT (`python -m sam.launcher.desktop`) dan
docker-compose. Men-delegasikan startup ke pipeline launcher yang sama
dengan entry `sam-desktop` (sam.launcher.cli_entry:desktop_main).
"""

import sys


def main() -> None:
    """Launch desktop mode via launcher pipeline."""
    # Delegasi ke desktop_main di cli_entry — satu sumber startup.
    from sam.launcher.cli_entry import desktop_main, _ensure_path

    _ensure_path()
    desktop_main()


if __name__ == "__main__":
    main()
    sys.exit(0)
