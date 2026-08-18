import pytest
from qdw_forge.db import Database

def test_migrate_creates_all_tables(tmp_path):
    db = Database(tmp_path / 'test.db')
    db.migrate()
    with db.connect() as con:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
    assert 'assets' in tables
    assert 'leases' in tables
    assert 'invocations' in tables
    assert 'asset_profiles' in tables
    assert 'frontier_candidates' in tables
    assert 'repo_bench_tasks' in tables
    assert 'asset_capabilities' in tables

def test_migrate_idempotent(tmp_path):
    db = Database(tmp_path / 'test.db')
    db.migrate()
    db.migrate()  # second call should not fail
    with db.connect() as con:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert len(tables) >= 7

def test_tx_commits(tmp_path):
    db = Database(tmp_path / 'test.db')
    db.migrate()
    with db.tx(immediate=True) as con:
        con.execute("INSERT INTO assets(asset_id,version,kind,name,status,manifest_json,manifest_hash,created_at) VALUES(?,?,?,?,?,?,?,?)",
                     ('a','1','SERVICE','test','CANDIDATE','{}','sha256:x','2026-01-01'))
    with db.connect() as con:
        r = con.execute("SELECT asset_id FROM assets WHERE asset_id='a'").fetchone()
    assert r is not None

def test_tx_rollback_on_error(tmp_path):
    db = Database(tmp_path / 'test.db')
    db.migrate()
    try:
        with db.tx(immediate=True) as con:
            con.execute("INSERT INTO assets(asset_id,version,kind,name,status,manifest_json,manifest_hash,created_at) VALUES(?,?,?,?,?,?,?,?)",
                         ('a','1','SERVICE','test','CANDIDATE','{}','sha256:x','2026-01-01'))
            raise ValueError("boom")
    except ValueError:
        pass
    with db.connect() as con:
        r = con.execute("SELECT asset_id FROM assets WHERE asset_id='a'").fetchone()
    assert r is None  # rolled back

def test_foreign_key_enforcement(tmp_path):
    db = Database(tmp_path / 'test.db')
    db.migrate()
    with db.connect() as con:
        with pytest.raises(Exception):  # foreign key violation
            con.execute("INSERT INTO asset_capabilities(asset_id,version,capability) VALUES('nonexist','1','x')")
