"""test_m12_010_secret_boundary.py — M12-010 Secret Boundary Hardening.

Produksi (SAM_ENV=production):
  - secret store REQUIRED -> default_secret_provider() HARUS memakai
    PgSecretProvider strict (bukan env-only).
  - master key hilang -> BLOCKED (SecretUnavailableError), BUKAN auto-gen.
  - store tidak tersedia / key tak ada di store -> BLOCKED, TANPA fallback
    diam-diam ke env (no silent env fallback).

Dev (tanpa SAM_ENV=production):
  - boleh fallback env; auto-gen master key boleh.
"""
from __future__ import annotations

import os

import pytest

from sam.runtime_service.secrets.secret_provider import (
    SecretProvider,
    default_secret_provider,
)
from sam.runtime_service.secrets.pg_secret_provider import (
    PgSecretProvider,
    SecretUnavailableError,
)


def test_dev_without_pg_uses_env_provider(monkeypatch):
    monkeypatch.delenv("SAM_ENABLE_PG_SECRETS", raising=False)
    monkeypatch.delenv("SAM_ENV", raising=False)
    p = default_secret_provider()
    assert isinstance(p, SecretProvider)
    assert not isinstance(p, PgSecretProvider)


def test_dev_optin_pg_is_non_strict(monkeypatch):
    monkeypatch.setenv("SAM_ENABLE_PG_SECRETS", "1")
    monkeypatch.delenv("SAM_ENV", raising=False)
    p = default_secret_provider()
    assert isinstance(p, PgSecretProvider)
    assert p.is_strict() is False  # dev: boleh auto-gen + fallback env


def test_production_forces_strict_pg(monkeypatch):
    monkeypatch.setenv("SAM_ENV", "production")
    monkeypatch.delenv("SAM_ENABLE_PG_SECRETS", raising=False)  # tak perlu diset
    p = default_secret_provider()
    assert isinstance(p, PgSecretProvider)
    assert p.is_strict() is True  # produksi: secret store REQUIRED


def test_strict_missing_master_key_blocks_not_autogen(tmp_path):
    # master key file TIDAK ada -> BLOCKED, bukan auto-gen
    missing = tmp_path / "no_master.key"
    p = PgSecretProvider(
        dsn="host=127.0.0.1 port=9 dbname=x user=x",  # tak valid; store tak tersedia
        master_key_path=str(missing),
        strict=True,
    )
    with pytest.raises(SecretUnavailableError):
        p.get("GITHUB_TOKEN")
    # BUKAN auto-gen: file tetap tidak dibuat
    assert not missing.exists()


def test_strict_no_silent_env_fallback(monkeypatch, tmp_path):
    # master key ADA, tapi store tidak tersedia + key di env
    # -> BLOCKED (jangan jatuh ke env diam-diam)
    key_file = tmp_path / "master.key"
    key_file.write_text("Y2U6gJfpzY0nURuA0jfH2mVm3RnpWqVt3_kXxTn9o0A=", encoding="utf-8")
    env = {"GITHUB_TOKEN": "env-plaintext-punya-penyerang"}
    p = PgSecretProvider(
        dsn="host=127.0.0.1 port=9 dbname=x user=x",  # store tak tersedia
        master_key_path=str(key_file),
        strict=True,
        env=env,
    )
    with pytest.raises(SecretUnavailableError):
        p.get("GITHUB_TOKEN")
    # env tidak boleh ter-ekspos (secret tetap rahasia; tidak kembalikan env)
    assert p.get  # (raise di atas sudah bukti no-fallback)


def test_dev_falls_back_to_env(monkeypatch, tmp_path):
    # dev: store tak ada -> fallback ke env (perilaku lama dipertahankan)
    key_file = tmp_path / "dev_master.key"
    key_file.write_text("Y2U6gJfpzY0nURuA0jfH2mVm3RnpWqVt3_kXxTn9o0A=", encoding="utf-8")
    env = {"SAMPG_TOKEN": "dev-env-value"}
    p = PgSecretProvider(
        dsn="host=127.0.0.1 port=9 dbname=x user=x",  # tak valid; store tak ada
        master_key_path=str(key_file),
        strict=False,
        env=env,
    )
    assert p.get("SAMPG_TOKEN") == "dev-env-value"


def test_dev_master_key_autogen(tmp_path):
    # dev: master key belum ada -> auto-generate (bukan BLOCKED)
    missing = tmp_path / "autogen_master.key"
    p = PgSecretProvider(
        dsn="host=127.0.0.1 port=9 dbname=x user=x",
        master_key_path=str(missing),
        strict=False,
        allow_auto_key=True,
    )
    # pemanggilan _load_or_create_key terjadi saat encrypt/get store
    key = p._load_or_create_key()
    assert key
    assert missing.exists()  # auto-gen membuat file
