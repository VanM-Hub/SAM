"""Unified Intelligence Runtime - Program E (v28.0.0).

Entry point untuk menyatukan representasi runtime SAM:
Registry -> Graph -> Context -> Validation -> Assembly -> Report.
Preview-only, synchronous, tanpa inference/LLM.
"""
from .intelligence_pipeline import FINAL_PIPELINE, IntelligencePipeline
from .intelligence_runtime import IntelligenceRuntime
from .integration import IntelligenceIntegration

__all__ = [
    "FINAL_PIPELINE",
    "IntelligencePipeline",
    "IntelligenceRuntime",
    "IntelligenceIntegration",
]
