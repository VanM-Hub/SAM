"""Shared fixtures for Compliance CLI tests."""

import pytest

from sam.compliance.catalog import ComplianceCheckCatalog
from sam.compliance.manifest import ManifestLoader
from sam.compliance.cli.session_runner import SessionRunner
from sam.compliance.cli.compliance_cli import ComplianceCLI
from sam.compliance.cli.exit_code_resolver import ExitCodeResolver


@pytest.fixture
def catalog():
    return ComplianceCheckCatalog()


@pytest.fixture
def manifest(catalog):
    return ManifestLoader(catalog).load()


@pytest.fixture
def runner(catalog, manifest):
    return SessionRunner(manifest, catalog)


@pytest.fixture
def cli(catalog, manifest):
    return ComplianceCLI(manifest=manifest, catalog=catalog)


@pytest.fixture
def exit_codes():
    return ExitCodeResolver()
