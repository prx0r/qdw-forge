from qdw_forge.models import CapabilityAsset,AssetKind,TransportSpec,TransportKind,AssetStatus

def mk(id,price): return CapabilityAsset(asset_id=id,version='1',kind=AssetKind.SERVICE,name=id,capabilities=['x'],transport=TransportSpec(kind=TransportKind.HTTP,endpoint='https://example.invalid'),pricing={'per_call':price},declared_quality=.9,status=AssetStatus.ACTIVE,certificate_id='cert')

def test_router_uses_verified_history_only(forge):
    forge.store.register_asset(mk('a',.4)); forge.store.register_asset(mk('b',.1))
    chosen,_=forge.router.choose('x'); assert chosen.asset_id=='b'
    # Strong verified history can change selection; requires certificates for every update.
    for i in range(20): forge.store.record_verified('a','1','x',success=True,cost_usd=.01,certificate_id=f'c{i}')
    for i in range(8): forge.store.record_verified('b','1','x',success=False,cost_usd=.1,certificate_id=f'd{i}')
    chosen,d=forge.router.choose('x'); assert chosen.asset_id=='a'; assert d.decision_hash.startswith('sha256:')

def test_profile_rejects_unverified_update(forge):
    forge.store.register_asset(mk('a',.1))
    import pytest
    with pytest.raises(ValueError): forge.store.record_verified('a','1','x',success=True,cost_usd=.1,certificate_id='')
