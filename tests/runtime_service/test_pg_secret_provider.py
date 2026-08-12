"""Test PgSecretProvider (M11-003 Production Secrets).

Verifikasi secret manager PostgreSQL terenkripsi:
  - set/get roundtrip (dekripsi benar)
  - nilai tidak tersimpan plaintext di DB (ciphertext Fernet)
  - fallback ke env bila key tidak ada di store
  - tidak ada bootstrap key / value di log audit
  - kompatibilitas kontrak SecretProvider (get/has/resolve_all/required)
"""
import os

import pytest

from sam.runtime_service.secrets.pg_secret_provider import PgSecretProvider


@pytest.fixture
def dsn():
    """DSN PostgreSQL nyata dari env (skipped bila tidak diset)."""
    value = os.environ.get("SAM_PG_DSN")
    if not value:
        pytest.skip("SAM_PG_DSN tidak diset - lewati (butuh PostgreSQL)")
    return value


@pytest.fixture
def provider(tmp_path, dsn):
    """Provider dengan master key file sementara + DSN PG nyata."""
    return PgSecretProvider(
        dsn=dsn,
        env={},  # env kosong -> uji store murni; fallback env diuji terpisah
        master_key_path=str(tmp_path / "master.key"),
        allow_auto_key=True,
    )


@pytest.fixture
def env_provider(tmp_path):
    """Provider dengan env-injeksi untuk uji fallback (tidak butuh PG)."""
    return PgSecretProvider(
        env={"SOMETHING": "envval"},
        master_key_path=str(tmp_path / "master.env.key"),
        allow_auto_key=True,
    )


class TestMasterKey:
    def test_key_file_auto_generated(self, tmp_path):
        p = PgSecretProvider(master_key_path=str(tmp_path / "k.key"))
        # force load key
        p._load_or_create_key()
        kf = tmp_path / "k.key"
        assert kf.exists()
        content = kf.read_text(encoding="utf-8").strip()
        # Fernet key = urlsafe base64, panjang 44
        assert len(content) == 44


class TestRoundTrip:
    def test_set_get_roundtrip(self, provider):
        assert provider.set_secret("GITHUB_TOKEN", "dummy_token_for_pg_test_123") is True
        assert provider.get("GITHUB_TOKEN") == "dummy_token_for_pg_test_123"

    def test_reuse_same_key_file_across_instances(self, tmp_path, provider):
        provider.set_secret("K", "value_v1")
        p2 = PgSecretProvider(master_key_path=str(tmp_path / "master.key"))
        assert p2.get("K") == "value_v1"

    def test_update_overwrites(self, provider):
        provider.set_secret("K", "v1")
        provider.set_secret("K", "v2")
        assert provider.get("K") == "v2"


class TestEncryptionAtRest:
    def test_no_plaintext_in_db(self, provider):
        # provider sudah pakai dsn nyata (fixture skip bila tak ada)
        provider.set_secret("AT_REST", "PLAINTEXT_MARKER_777")
        stored = provider._store_get("AT_REST")
        assert "PLAINTEXT_MARKER_777" not in stored
        assert stored.startswith("gAAAAA")  # Fernet magic
        provider.delete_secret("AT_REST")


class TestFallbackEnv:
    def test_missing_key_falls_back_to_env(self, env_provider):
        # key tidak ada di store -> fallback baca env
        assert env_provider.get("SOMETHING") == "envval"

    def test_has_respects_env_and_store(self, provider, env_provider):
        provider.set_secret("STORE_KEY", "x")
        assert provider.has("STORE_KEY") is True   # dari store
        assert env_provider.has("SOMETHING") is True  # dari env fallback
        assert env_provider.has("NOPE") is False
        assert provider.has("SOMETHING") is False  # env provider kosong, tidak di store

    def test_required_raises_when_missing(self, env_provider):
        with pytest.raises(KeyError):
            env_provider.required("MISSING")


class TestAuditMasked:
    def test_audit_never_contains_raw(self, provider):
        provider.set_secret("A", "raw-secret-99")
        provider.get("A")
        for rec in provider.audit()["access"]:
            text = str(rec)
            assert "raw-secret-99" not in text
            assert "key" in rec
