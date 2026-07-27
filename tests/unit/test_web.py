"""
Unit tests — Web Dashboard (Phase 1)
"""

import pytest
from sam.web.server import app


class TestWebRoutes:
    def test_app_created(self):
        assert app.title == "SAM Operations Console"

    def test_routes_registered(self):
        routes = {r.path for r in app.routes}
        assert "/" in routes
        assert "/runtime" in routes
        assert "/workflow" in routes
        assert "/incidents" in routes
        assert "/autonomous" in routes
        assert "/openclaw" in routes
        assert "/knowledge" in routes
        assert "/settings" in routes
        assert "/static" in routes or any("/static" in str(r) for r in app.routes)

    def test_cors_configured(self):
        middlewares = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middlewares

    def test_templates_directory(self):
        from pathlib import Path
        web_templates = Path("D:/Project AI/SAM/src/sam/web/templates")
        assert (web_templates / "base.html").exists()
        assert (web_templates / "index.html").exists()
        assert (web_templates / "runtime.html").exists()
        assert (web_templates / "workflow.html").exists()
        assert (web_templates / "incidents.html").exists()
        assert (web_templates / "autonomous.html").exists()
        assert (web_templates / "openclaw.html").exists()
        assert (web_templates / "knowledge.html").exists()
        assert (web_templates / "settings.html").exists()

    def test_run_server_import(self):
        from sam.web.server import run_server
        assert callable(run_server)


class TestWebCLIIntegration:
    def test_web_command_in_main(self):
        from sam.cli.main import app as cli_app
        # Check if web is registered as a command or typer command
        # It's a @app.command() so check registered_commands
        cmds = [c.name for c in cli_app.registered_commands if c.name]
        assert "web" in cmds or any(
            hasattr(c, "callback") and c.callback and c.callback.__name__ == "web"
            for c in cli_app.registered_commands
        )

    def test_static_files_exist(self):
        from pathlib import Path
        web_dir = Path(__file__).parent.parent.parent / "src" / "sam" / "web"
        assert (web_dir / "static" / "css" / "style.css").exists()
