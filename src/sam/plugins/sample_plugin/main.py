"""
Sample plugin main module.

This is a stub implementation for testing and demonstration purposes.
"""

import structlog

logger = structlog.get_logger()


async def initialize(context):
    """Initialize the sample plugin."""
    logger.info("sample_plugin_initialized", context=context.__class__.__name__)
    return {"status": "initialized"}


async def shutdown():
    """Shutdown the sample plugin."""
    logger.info("sample_plugin_shutdown")
    return {"status": "shutdown"}


async def health():
    """Health check for the sample plugin."""
    return {"status": "healthy", "message": "Sample plugin is healthy"}