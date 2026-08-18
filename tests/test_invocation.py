from qdw_forge.models import CapabilityAsset,AssetKind,TransportSpec,TransportKind,AssetStatus,LeaseRequest,InvocationRequest,InvocationStatus
class FakeDispatcher:
    def invoke(self,asset,args): return {'echo':args['text']},.02

def test_invocation_stays_unverified_until_certificate(forge):
    a=CapabilityAsset(asset_id='echo',version='1',kind=AssetKind.SERVICE,name='Echo',capabilities=['echo'],transport=TransportSpec(kind=TransportKind.HTTP,endpoint='https://unused'),status=AssetStatus.ACTIVE,certificate_id='asset-cert',input_schema={'type':'object','required':['text'],'properties':{'text':{'type':'string'}},'additionalProperties':False},output_schema={'type':'object','required':['echo'],'properties':{'echo':{'type':'string'}}})
    forge.store.register_asset(a); forge.invocations.dispatcher=FakeDispatcher()
    lease,token=forge.leases.create(LeaseRequest(capability='echo'))
    r=forge.invocations.invoke(InvocationRequest(lease_token=token,capability='echo',arguments={'text':'hi'},client_request_id='r1'))
    assert r.status==InvocationStatus.SUCCEEDED_UNVERIFIED
    assert forge.store.profile('echo','1','echo').sample_count==0
    forge.invocations.bind_verification(r.invocation_id,certificate_id='verify-cert',passed=True)
    r2=forge.invocations.get(r.invocation_id); assert r2.status==InvocationStatus.VERIFIED
    assert forge.store.profile('echo','1','echo').sample_count==1

def test_idempotent_client_request(forge):
    a=CapabilityAsset(asset_id='echo',version='1',kind=AssetKind.SERVICE,name='Echo',capabilities=['echo'],transport=TransportSpec(kind=TransportKind.HTTP,endpoint='https://unused'),status=AssetStatus.ACTIVE,certificate_id='cert')
    forge.store.register_asset(a); forge.invocations.dispatcher=FakeDispatcher(); _,token=forge.leases.create(LeaseRequest(capability='echo',calls=2))
    req=InvocationRequest(lease_token=token,capability='echo',arguments={'text':'a'},client_request_id='same')
    x=forge.invocations.invoke(req); y=forge.invocations.invoke(req); assert x.invocation_id==y.invocation_id
