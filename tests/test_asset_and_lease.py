import pytest
from qdw_forge.models import CapabilityAsset,AssetKind,TransportSpec,TransportKind,AssetStatus,LeaseRequest

def asset(status=AssetStatus.CANDIDATE,certificate_id=None,version='1'):
    return CapabilityAsset(asset_id='factory.echo',version=version,kind=AssetKind.FACTORY,name='Echo',capabilities=['text.echo'],transport=TransportSpec(kind=TransportKind.HTTP,endpoint='https://example.invalid/echo'),declared_quality=.9,status=status,certificate_id=certificate_id)

def test_active_requires_certificate():
    with pytest.raises(ValueError): asset(AssetStatus.ACTIVE,None)

def test_immutable_version(forge):
    forge.store.register_asset(asset())
    changed=asset().model_copy(update={'name':'Changed'})
    with pytest.raises(ValueError): forge.store.register_asset(changed)

def test_activate_then_lease(forge):
    forge.store.register_asset(asset()); forge.store.activate('factory.echo','1','cert_real_1')
    lease,token=forge.leases.create(LeaseRequest(capability='text.echo',calls=2,max_spend_usd=1))
    assert lease.asset_id=='factory.echo'; assert token.count('.')==2
    assert forge.leases.verify(token,'text.echo').lease_id==lease.lease_id
    with pytest.raises(PermissionError): forge.leases.verify(token,'other.cap')
