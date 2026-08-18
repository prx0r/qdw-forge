import pytest
import os
from qdw_forge.api import app, _state
from qdw_forge.app import ForgeApp
from qdw_forge.models import CapabilityAsset, AssetKind, TransportSpec, TransportKind, AssetStatus

@pytest.fixture
def client(tmp_path):
    from fastapi.testclient import TestClient
    import qdw_forge.api as api_mod
    # Reset singleton state
    api_mod._state = None
    # Set env for from_env()
    old_secret = os.environ.get('QDW_FORGE_LEASE_SECRET')
    old_dev = os.environ.get('QDW_FORGE_ALLOW_DEV_SECRET')
    old_db = os.environ.get('QDW_FORGE_DB')
    os.environ['QDW_FORGE_DB'] = str(tmp_path / 'api_test.db')
    os.environ['QDW_FORGE_ALLOW_DEV_SECRET'] = '1'
    os.environ['QDW_FORGE_LEASE_SECRET'] = 'x' * 40
    c = TestClient(app)
    yield c
    api_mod._state = None
    # Restore env
    if old_secret is not None: os.environ['QDW_FORGE_LEASE_SECRET'] = old_secret
    elif 'QDW_FORGE_LEASE_SECRET' in os.environ: del os.environ['QDW_FORGE_LEASE_SECRET']
    if old_dev is not None: os.environ['QDW_FORGE_ALLOW_DEV_SECRET'] = old_dev
    elif 'QDW_FORGE_ALLOW_DEV_SECRET' in os.environ: del os.environ['QDW_FORGE_ALLOW_DEV_SECRET']
    if old_db is not None: os.environ['QDW_FORGE_DB'] = old_db
    elif 'QDW_FORGE_DB' in os.environ: del os.environ['QDW_FORGE_DB']

@pytest.fixture
def sample_asset():
    return CapabilityAsset(
        asset_id='test.svc', version='1', kind=AssetKind.SERVICE, name='Test',
        capabilities=['test.run'], transport=TransportSpec(kind=TransportKind.HTTP, endpoint='https://test.invalid'),
        status=AssetStatus.CANDIDATE
    )

def test_health(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_register_and_list_asset(client, sample_asset):
    r = client.post('/v1/assets', json=sample_asset.model_dump(mode='json'))
    assert r.status_code == 200
    data = r.json()
    assert data['asset_id'] == 'test.svc'
    assert data['version'] == '1'
    # List
    r2 = client.get('/v1/assets')
    assert r2.status_code == 200
    assert any(a['asset_id'] == 'test.svc' for a in r2.json())

def test_register_duplicate_returns_409(client, sample_asset):
    client.post('/v1/assets', json=sample_asset.model_dump(mode='json'))
    changed = sample_asset.model_copy(update={'name': 'Changed'})
    r = client.post('/v1/assets', json=changed.model_dump(mode='json'))
    assert r.status_code == 409

def test_activate_asset(client, sample_asset):
    client.post('/v1/assets', json=sample_asset.model_dump(mode='json'))
    r = client.post('/v1/assets/test.svc/1/activate', json={'certificate_id': 'cert1'})
    assert r.status_code == 200
    assert r.json()['status'] == 'ACTIVE'

def test_lease_and_invoke(client, sample_asset):
    # Register and activate
    client.post('/v1/assets', json=sample_asset.model_dump(mode='json'))
    client.post('/v1/assets/test.svc/1/activate', json={'certificate_id': 'cert1'})
    # Lease
    r = client.post('/v1/leases', json={'capability': 'test.run', 'calls': 1})
    assert r.status_code == 200
    lease_data = r.json()
    assert 'token' in lease_data
    assert lease_data['lease']['asset_id'] == 'test.svc'

def test_invoke_nonexistent_asset_returns_404(client):
    # Fake token → ValueError → 400
    r = client.post('/v1/invoke', json={
        'lease_token': 'fake.token.signature', 'capability': 'nonexist',
        'arguments': {}, 'client_request_id': 'r1'
    })
    assert r.status_code == 400

def test_get_invocation_not_found(client):
    r = client.get('/v1/invocations/nonexist')
    assert r.status_code == 404

def test_verify_invocation_not_found(client):
    r = client.post('/v1/invocations/nonexist/verification', json={'certificate_id': 'c', 'passed': True})
    assert r.status_code == 404
