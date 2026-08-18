import pytest
from qdw_forge.tokens import LeaseTokenSigner
from qdw_forge.models import CapabilityAsset,AssetKind,TransportSpec,TransportKind,AssetStatus,LeaseRequest

def test_tampered_token_rejected():
    s=LeaseTokenSigner(b'x'*32); t=s.issue({'lease_id':'l','cap':'x','exp':9999999999})
    bad=t[:-1]+('A' if t[-1]!='A' else 'B')
    with pytest.raises(ValueError): s.verify(bad)

def test_call_and_spend_limits(forge):
    a=CapabilityAsset(asset_id='x',version='1',kind=AssetKind.SERVICE,name='x',capabilities=['x'],transport=TransportSpec(kind=TransportKind.HTTP,endpoint='https://unused'),pricing={'per_call':.2},status=AssetStatus.ACTIVE,certificate_id='c')
    forge.store.register_asset(a); l,t=forge.leases.create(LeaseRequest(capability='x',calls=1,max_spend_usd=.3)); forge.leases.consume(l.lease_id,.2)
    with pytest.raises(PermissionError): forge.leases.consume(l.lease_id,.2)
