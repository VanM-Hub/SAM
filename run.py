"""
Runtime Launcher — Entry point SAM Operations Console.

Menjalankan:
1. Telemetry Service (event collector)
2. Health Server (port 8181)
3. Desktop Operations Console (PySide6)

Usage:
    python run.py             # Full stack
    python run.py --headless  # Tanpa desktop (server only)
    python run.py --health    # Health server only
"""

import argparse
import asyncio
import sys
import os
import structlog

logger = structlog.get_logger()

VERSION = "3.2.1"


def main():
    parser = argparse.ArgumentParser(description="SAM Operations Console")
    parser.add_argument("--headless", action="store_true", help="Run without desktop UI")
    parser.add_argument("--health", action="store_true", help="Health server only")
    parser.add_argument("--version", action="store_true", help="Show version")
    args = parser.parse_args()

    if args.version:
        print(f"SAM Operations Console v{VERSION}")
        sys.exit(0)

    # Pastikan PYTHONPATH
    src = os.path.join(os.path.dirname(__file__), "src")
    if src not in sys.path:
        sys.path.insert(0, os.path.abspath(src))

    if args.health:
        _run_health_only()
    elif args.headless:
        _run_headless()
    else:
        _run_full()


def _run_health_only():
    """Health server only."""
    async def _run():
        from sam.operations.health import HealthServer
        server = HealthServer()
        await server.start()
        logger.info("sam.running.health_only")
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await server.stop()

    asyncio.run(_run())


def _run_headless():
    """Server mode — telemetry + health."""
    async def _run():
        from sam.telemetry.service import TelemetryService
        from sam.operations.health import HealthServer

        telemetry = TelemetryService()
        server = HealthServer()

        await telemetry.start()
        server.mark_ready(telemetry=True)
        await server.start()

        logger.info("sam.running.headless")
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            await server.stop()
            await telemetry.stop()

    asyncio.run(_run())


def _run_full():
    """Full stack — telemetry + health + desktop."""
    import threading

    # Start server in background
    def start_services():
        async def _run():
            from sam.telemetry.service import TelemetryService
            from sam.operations.health import HealthServer

            telemetry = TelemetryService()
            server = HealthServer()

            await telemetry.start()
            server.mark_ready(telemetry=True)
            await server.start()

            logger.info("sam.running.full_server")
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                await server.stop()
                await telemetry.stop()

        asyncio.run(_run())

    svc = threading.Thread(target=start_services, daemon=True)
    svc.start()

    # Start desktop
    from sam.desktop.main import run
    run()


if __name__ == "__main__":
    main()
