"""Shared fixtures for Compliance Baseline tests."""

import pytest

from sam.compliance.baseline import BaselineLoader, BaselineIndex, BaselineSerializer


@pytest.fixture
def loader():
    return BaselineLoader()


@pytest.fixture
def snapshot(loader):
    return loader.load()


@pytest.fixture
def index(snapshot):
    return BaselineIndex(snapshot)


@pytest.fixture
def serializer():
    return BaselineSerializer()
