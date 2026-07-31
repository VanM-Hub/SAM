"""Secrets Runtime (Sprint 263).

Program D - Runtime Services & Deployment.
Semua secret dari environment. Tidak pernah hardcode.
"""
from __future__ import annotations

SECRETS_RUNTIME_VERSION = "27.0.0"

# Secret keys yang didukung (env)
SUPPORTED_SECRETS = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY",
    "OPENCLAW_URL",
    "OLLAMA_HOST",
)
