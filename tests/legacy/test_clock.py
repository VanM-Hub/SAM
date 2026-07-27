import asyncio
import sys
from datetime import datetime, timedelta

from src.sam.core.clock import SystemClock, FrozenClock, VirtualClock


async def test_system_clock():
    clk = SystemClock()
    now = clk.now()
    assert isinstance(now, datetime)
    # Real clock should move forward
    await clk.sleep(0.01)
    later = clk.now()
    assert later >= now
    print("system_clock: OK")


async def test_frozen_clock():
    fixed = datetime(2025, 6, 15, 10, 30, 0)
    clk = FrozenClock(fixed_time=fixed)
    assert clk.now() == fixed
    # Frozen clock never advances
    await clk.sleep(999)
    assert clk.now() == fixed
    # Manual set_time
    clk.set_time(datetime(2026, 7, 24, 12, 0, 0))
    assert clk.now() == datetime(2026, 7, 24, 12, 0, 0)
    print("frozen_clock: OK")


async def test_virtual_clock():
    start = datetime(2026, 1, 1, 0, 0, 0)
    clk = VirtualClock(start_time=start)
    assert clk.now() == start

    # Sleep advances immediately
    await clk.sleep(30)
    assert clk.now() == start + timedelta(seconds=30)

    # Tick does the same
    await clk.tick(15)
    assert clk.now() == start + timedelta(seconds=45)

    # Manual advance
    clk.advance(10)
    assert clk.now() == start + timedelta(seconds=55)

    # Reset
    clk.reset()
    assert clk.now() == start
    print("virtual_clock: OK")


async def test_virtual_clock_custom_advance():
    clk = VirtualClock()
    initial = clk.now()
    clk.advance(3600)
    assert clk.now() == initial + timedelta(seconds=3600)
    print("virtual_clock_custom_advance: OK")


async def test_clock_in_health():
    """Verify ServiceHealth uses clock argument correctly."""
    from src.sam.core.health import ServiceHealth

    fixed = datetime(2025, 1, 1)
    frozen = FrozenClock(fixed_time=fixed)

    # Without clock argument (uses SystemClock)
    h1 = ServiceHealth.healthy("no clock")
    assert h1.last_check is not None

    # With frozen clock
    h2 = ServiceHealth.healthy("with clock", clock=frozen)
    assert h2.last_check == fixed

    # degraded with clock
    h3 = ServiceHealth.degraded("degraded", clock=frozen)
    assert h3.last_check == fixed

    print("clock_in_health: OK")


if __name__ == "__main__":
    tests = [
        test_system_clock,
        test_frozen_clock,
        test_virtual_clock,
        test_virtual_clock_custom_advance,
        test_clock_in_health,
    ]
    for t in tests:
        try:
            asyncio.run(t())
        except Exception as e:
            print(f"{t.__name__}: FAILED ({e})")
            sys.exit(1)
    print("ALL PASSED")
    sys.exit(0)
