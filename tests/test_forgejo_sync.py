import base64, httpx, yaml
from qdw_forge.forgejo import ForgejoClient,ForgejoSync

def test_sync_reads_agent_manifest(forge):
    doc={'assets':[{'asset_id':'f','version':'1','kind':'SERVICE','name':'f','capabilities':['x'],'transport':{'kind':'HTTP','endpoint':'https://unused'},'status':'ACTIVE','certificate_id':'cert'}]}
    def handler(req):
        if req.url.path.endswith('/orgs/qdw/repos'): return httpx.Response(200,json=[{'name':'r','default_branch':'main'}])
        if '/contents/qdw.yaml' in req.url.path: return httpx.Response(200,json={'content':base64.b64encode(yaml.safe_dump(doc).encode()).decode()})
        return httpx.Response(404)
    client=httpx.Client(transport=httpx.MockTransport(handler)); fc=ForgejoClient('https://forge.invalid','t',client=client)
    stats=ForgejoSync(fc,forge.store).sync_org('qdw'); assert stats['assets']==1; assert forge.store.candidates('x')[0].asset_id=='f'
