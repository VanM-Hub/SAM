"""Unit test fixtures: fixtures khusus untuk unit test."""
import pytest

@pytest.fixture
def sam(sam_instance):
    """SAM instance segar per test."""
    return sam_instance
