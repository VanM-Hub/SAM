"""
SAM Desktop Launcher.

Entry point untuk double-click execution.
Digunakan oleh launcher.bat (Windows) dan launcher.sh (Linux).
"""

import asyncio
import sys
from pathlib import Path
from ..runtime.coordinator import RuntimeCoordinator
from ..hosting.base import DesktopAdapter


async def main():
    """Start SAM Runtime from desktop launcher."""
    print("=" * 48)
    print("  SAM Framework v1.1.0")
    print("  Starting Runtime...")
    print("=" * 48)

    adapter = DesktopAdapter()
    coordinator = RuntimeCoordinator(adapter=adapter)

    try:
        # Bootstrap
        await coordinator.start()
        print(f"\n  State: {coordinator.state.value.upper()}")
        print(f"  Hosting: {coordinator.adapter_name}")
        print(f"  Session: {coordinator.session_manager.get_current_session()['id']}")

        # Run
        await coordinator.run()
        print(f"\n  {'=' * 48}")
        print(f"  SAM is READY.")
        print(f"  Press Ctrl+C to stop.")
        print(f"  {'=' * 48}")

        # Keep running forever
        await asyncio.Event().wait()

    except KeyboardInterrupt:
        print("\n\n  Shutting down...")
        await coordinator.stop()
        print("  SAM stopped gracefully.")
    except Exception as e:
        print(f"\n  Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
