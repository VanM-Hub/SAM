FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /opt/sam

# Copy source
COPY src/ ./src/
COPY workspace/ ./workspace/
COPY pyproject.toml ./

# Install runtime dependencies
RUN pip install --no-cache-dir -e . 2>/dev/null || \
    pip install --no-cache-dir structlog typer pydantic pyyaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from sam.cli.health import app; import typer; typer.echo('OK')" || exit 1

ENTRYPOINT ["python", "-m", "sam.launcher.desktop"]
