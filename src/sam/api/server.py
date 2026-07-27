"""
SAM Runtime API — Phase 1

FastAPI server dengan endpoints:
  - /health          — health check
  - /health/ready    — readiness probe
  - /runtime         — status runtime
  - /metrics         — metrics terkini
  - /events          — event telemetry

Run:
    uvicorn sam.api.server:app --host 0.0.0.0 --port 8080
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import health, runtime, events, metrics

app = FastAPI(
    title="SAM Runtime API",
    description="SAM — AI Operations Guardian Runtime API",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(runtime.router, prefix="/runtime", tags=["runtime"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])


@app.get("/")
async def root():
    return {
        "message": "SAM Runtime API",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "ready": "/health/ready",
            "runtime": "/runtime",
            "metrics": "/metrics",
            "events": "/events",
        },
    }
