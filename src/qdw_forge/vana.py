from __future__ import annotations
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol, Any
import httpx
from .models import DataRightsHandle

class AuthorizationProvider(Protocol):
    def header_for(self,*,method:str,uri:str,grant_id:str|None)->str: ...

@dataclass(frozen=True)
class StaticAuthorizationProvider:
    value:str
    def header_for(self,*,method:str,uri:str,grant_id:str|None)->str: return self.value

class VanaPersonalServerClient:
    """Protocol-level Vana Personal Server adapter.
    Signing/wallet custody stays outside QDW; this client accepts an authorization provider.
    """
    def __init__(self,base_url:str,auth:AuthorizationProvider,client:httpx.Client|None=None): self.base=base_url.rstrip('/'); self.auth=auth; self.client=client or httpx.Client()
    def _headers(self,method:str,uri:str,grant_id:str|None):
        h={"authorization":self.auth.header_for(method=method,uri=uri,grant_id=grant_id)}
        if grant_id: h['x-vana-grant-id']=grant_id
        return h
    def list_scopes(self,grant_id:str)->dict[str,Any]:
        uri='/v1/data'; r=self.client.get(self.base+uri,headers=self._headers('GET',uri,grant_id)); r.raise_for_status(); return r.json()
    def read_scope(self,grant_id:str,scope:str,*,at:str|None=None)->dict[str,Any]:
        uri=f'/v1/data/{scope}'; params={'at':at} if at else None
        r=self.client.get(self.base+uri,headers=self._headers('GET',uri,grant_id),params=params); r.raise_for_status(); return r.json()
    def versions(self,grant_id:str,scope:str)->dict[str,Any]:
        uri=f'/v1/data/{scope}/versions'; r=self.client.get(self.base+uri,headers=self._headers('GET',uri,grant_id)); r.raise_for_status(); return r.json()

def assert_rights(handle:DataRightsHandle,*,scope:str,operation:str='read'):
    if handle.expires_at and handle.expires_at < datetime.now(UTC): raise PermissionError('data rights expired')
    if scope not in handle.scopes: raise PermissionError('scope outside data grant')
    if operation not in handle.operations: raise PermissionError('operation outside data grant')
    if operation=='raw_export' and not handle.raw_export: raise PermissionError('raw export forbidden')
