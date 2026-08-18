import httpx
from qdw_forge.invokers import A2AInvoker
from qdw_forge.models import CapabilityAsset,AssetKind,AssetStatus,TransportSpec,TransportKind

def test_a2a_completed_task_is_concrete_result():
    def h(req):
        assert req.headers['A2A-Version']=='1.0'
        return httpx.Response(200,json={'id':'t1','status':{'state':'completed'},'artifacts':[{'artifactId':'a1','parts':[{'data':{'ok':True}}]}]})
    a=CapabilityAsset(asset_id='agent',version='1',kind=AssetKind.AGENT,name='a',capabilities=['x'],transport=TransportSpec(kind=TransportKind.A2A,endpoint='https://agent.invalid/tasks'),status=AssetStatus.ACTIVE,certificate_id='cert')
    out,cost=A2AInvoker(httpx.Client(transport=httpx.MockTransport(h))).invoke(a,{'x':1})
    assert out['task_id']=='t1' and out['artifacts'][0]['artifactId']=='a1'
