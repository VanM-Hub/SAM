"""
SAM — Shared test fixtures.

Menyediakan fixture dasar untuk semua test unit.
"""

import sys
import os
import pytest

# ============================================================================
# Fixture: SAM Instance
# ============================================================================

@pytest.fixture(scope="session")
def sam_instance():
    """Satu SAM instance untuk sesi test.

    Cukup satu kali karena SAM adalah singleton-like.
    """
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from sam.operations.conversation_api import SAM
    return SAM()


@pytest.fixture
def sam(sam_instance):
    """SAM instance segar per test.

    Menggunakan session fixture di belakang layar untuk efisiensi.
    """
    return sam_instance


@pytest.fixture
def conversation(sam):
    """Conversation object dari SAM.observe()."""
    return sam.observe()


@pytest.fixture
def conversation_with_answer(conversation):
    """Conversation dengan satu 'status' call."""
    conversation.answer("Status sistem?")
    return conversation


# ============================================================================
# Fixture: Sederhana cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def _cleanup_loggers():
    """Bersihkan logger sebelum tiap test (mencegah leak antar test)."""
    import structlog
    structlog.reset_defaults()
    yield
