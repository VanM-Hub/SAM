import asyncio
import sys
import uuid
from datetime import datetime

from src.sam.core.service import RuntimeService
from src.sam.core.service_manager import ServiceManager
from src.sam.core.health import ServiceHealth
from src.sam.core.event_bus import EventBus
from src.sam.core.events import ServiceStarted


class DummyService(RuntimeService):
    def __init__(self, name: str):
        super().__init__()
        self._name = name
        self.init_called = False
        self.start_called = False
        self.stop_called = False

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self) -> None:
        await asyncio.sleep(0)
        self.init_called = True

    async def start(self) -> None:
        await asyncio.sleep(0)
        self.start_called = True

    async def stop(self) -> None:
        await asyncio.sleep(0)
        self.stop_called = True

    async def health(self) -> ServiceHealth:
        return ServiceHealth.healthy(f"{self.name} OK at {datetime.utcnow().isoformat()}")


async def run_test():
    bus = EventBus()
    mgr = ServiceManager(bus)
    svc1 = DummyService("svc1")
    svc2 = DummyService("svc2")

    received = []

    async def on_service_started(ev):
        received.append((ev.type, ev.source, ev.id))

    # subscribe to service.started events
    bus.subscribe("service.started", on_service_started)

    # register
    mgr.register(svc1)
    mgr.register(svc2)

    # verify event bus injected
    assert getattr(svc1, "_event_bus", None) is bus

    print("Registered services:", mgr.list_services())

    # initialize
    await mgr.initialize_all()
    print("Initialized:", svc1.initialized, svc2.initialized)

    # start
    await mgr.start_all()
    print("Started:", svc1.started, svc2.started)

    # publish an event from a service via injected event bus
    ev = ServiceStarted(id=str(uuid.uuid4()), source=svc1.name, payload={})
    await svc1._event_bus.publish(ev)

    # allow handlers to run
    await asyncio.sleep(0)

    assert len(received) >= 1
    print('Received events:', received)

    # health
    health = await mgr.health_all()
    for name, h in health.items():
        print(f"Health {name}: {h.status} - {h.message}")

    # stop
    await mgr.stop_all()
    print("Stopped:", svc1.stopped, svc2.stopped)


if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except Exception as e:
        print("ERROR", e)
        sys.exit(1)
    print("OK")
    sys.exit(0)
