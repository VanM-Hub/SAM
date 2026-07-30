"""
Unit tests — FastAPI Endpoints (Phase 1)
"""

import pytest
from sam.api.routes.health import router as health_router
from sam.api.routes.runtime import router as runtime_router
from sam.api.routes.events import router as events_router
from sam.api.routes.metrics import router as metrics_router


class TestHealthRoutes:
    def test_router_exists(self):
        assert health_router is not None

    def test_routes_registered(self):
        routes = [r.path for r in health_router.routes]
        assert "/" in routes
        assert "/ready" in routes


class TestRuntimeRoutes:
    def test_router_exists(self):
        assert runtime_router is not None

    def test_root_route(self):
        routes = [r.path for r in runtime_router.routes]
        assert "/" in routes


class TestEventsRoutes:
    def test_router_exists(self):
        assert events_router is not None

    def test_root_route(self):
        routes = [r.path for r in events_router.routes]
        assert "/" in routes


class TestMetricsRoutes:
    def test_router_exists(self):
        assert metrics_router is not None

    def test_root_route(self):
        routes = [r.path for r in metrics_router.routes]
        assert "/" in routes


class TestAPIServer:
    def test_server_import(self):
        from sam.api.server import app
        assert app.title == "SAM Runtime API"
        assert app.version == "1.0"

    def test_server_root_endpoint(self):
        from sam.api.server import app
        routes = {r.path for r in app.routes}
        assert "/" in routes
        # FastAPI includes trailing slash by default for prefix routers
        assert "/health/" in routes or "/health" in routes
        assert "/health/ready" in routes
        assert "/runtime/" in routes or "/runtime" in routes
        assert "/events/" in routes or "/events" in routes
        assert "/metrics/" in routes or "/metrics" in routes

    def test_cors_middleware_configured(self):
        from sam.api.server import app
        middlewares = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middlewares
