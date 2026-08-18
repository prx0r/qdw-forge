import json, subprocess, sys, tempfile, os
from pathlib import Path

def run_cli(*args, db=None):
    env = {**os.environ, 'PYTHONPATH': str(Path(__file__).parent.parent / 'src'),
           'QDW_FORGE_ALLOW_DEV_SECRET': '1', 'QDW_FORGE_LEASE_SECRET': 'x' * 40}
    cmd = [sys.executable, '-m', 'qdw_forge.cli', '--db', str(db)] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    return r

def test_cli_init_db(tmp_path):
    db = tmp_path / 'test.db'
    r = run_cli('init-db', db=db)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data['status'] == 'ok'

def test_cli_register_and_list(tmp_path):
    db = tmp_path / 'test.db'
    manifest = {
        'asset_id': 'cli.test', 'version': '1', 'kind': 'SERVICE', 'name': 'CLI Test',
        'capabilities': ['cli.run'], 'transport': {'kind': 'HTTP', 'endpoint': 'https://test.invalid'},
        'status': 'CANDIDATE'
    }
    manifest_path = tmp_path / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest))
    r = run_cli('register', str(manifest_path), db=db)
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data['asset_id'] == 'cli.test'
    # List
    r2 = run_cli('assets', db=db)
    assert r2.returncode == 0
    assets = json.loads(r2.stdout)
    assert any(a['asset_id'] == 'cli.test' for a in assets)

def test_cli_parse_arxiv(tmp_path):
    atom = tmp_path / 'test.xml'
    atom.write_text("""<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'>
    <entry><id>https://arxiv.org/abs/1</id><title>Agent routing</title><summary>Methods for routing.</summary></entry>
    </feed>""")
    r = run_cli('parse-arxiv', str(atom), db=tmp_path / 'dummy.db')
    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert len(data) == 1
    assert 'router' in data[0]['extension_points']
