import pytest
from qdw_forge.app import ForgeApp

def test_forge_app_composition(tmp_path):
    app = ForgeApp(tmp_path / 'forge.db', b'test-secret-32-bytes-minimum-ok!')
    assert app.db is not None
    assert app.store is not None
    assert app.router is not None
    assert app.signer is not None
    assert app.leases is not None
    assert app.dispatcher is not None
    assert app.invocations is not None

def test_forge_app_migrates_on_init(tmp_path):
    app = ForgeApp(tmp_path / 'forge.db', b'test-secret-32-bytes-minimum-ok!')
    # Tables should exist
    with app.db.connect() as con:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert 'assets' in tables
    assert 'leases' in tables

def test_forge_app_from_env_dev(tmp_path, monkeypatch):
    monkeypatch.setenv('QDW_FORGE_DB', str(tmp_path / 'env.db'))
    monkeypatch.setenv('QDW_FORGE_ALLOW_DEV_SECRET', '1')
    monkeypatch.setenv('QDW_FORGE_LEASE_SECRET', '')
    from qdw_forge.app import from_env
    app = from_env()
    assert app.db is not None

def test_forge_app_from_env_requires_secret(tmp_path, monkeypatch):
    monkeypatch.setenv('QDW_FORGE_DB', str(tmp_path / 'env.db'))
    monkeypatch.delenv('QDW_FORGE_ALLOW_DEV_SECRET', raising=False)
    monkeypatch.setenv('QDW_FORGE_LEASE_SECRET', 'short')
    from qdw_forge.app import from_env
    with pytest.raises(RuntimeError, match="32 bytes"):
        from_env()
