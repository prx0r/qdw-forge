from __future__ import annotations
import base64
from typing import Any
import httpx, yaml
from .models import CapabilityAsset
from .store import ForgeStore

class ForgejoClient:
    def __init__(self,base_url:str,token:str,client:httpx.Client|None=None):
        self.base_url=base_url.rstrip('/'); self.token=token; self.client=client or httpx.Client()
    @property
    def headers(self): return {"authorization":f"token {self.token}","accept":"application/json"}
    def list_org_repos(self,org:str)->list[dict[str,Any]]:
        r=self.client.get(f"{self.base_url}/api/v1/orgs/{org}/repos",headers=self.headers,params={"limit":50}); r.raise_for_status(); return r.json()
    def get_file(self,owner:str,repo:str,path:str,ref:str|None=None)->bytes:
        params={"ref":ref} if ref else None
        r=self.client.get(f"{self.base_url}/api/v1/repos/{owner}/{repo}/contents/{path}",headers=self.headers,params=params); r.raise_for_status(); body=r.json()
        return base64.b64decode(body['content'])

class ForgejoSync:
    def __init__(self,client:ForgejoClient,store:ForgeStore): self.client=client; self.store=store
    def sync_org(self,org:str)->dict[str,int]:
        stats={"repos":0,"manifests":0,"assets":0,"errors":0}
        for repo in self.client.list_org_repos(org):
            stats['repos']+=1
            try: raw=self.client.get_file(org,repo['name'],'qdw.yaml',repo.get('default_branch'))
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code==404: continue
                stats['errors']+=1; continue
            try:
                doc=yaml.safe_load(raw) or {}; stats['manifests']+=1
                for item in doc.get('assets',[]):
                    asset=CapabilityAsset.model_validate(item); self.store.register_asset(asset); stats['assets']+=1
            except Exception: stats['errors']+=1
        return stats
