from __future__ import annotations
import json, os
from .app import from_env
from .models import LeaseRequest,InvocationRequest

def build_server():
    from mcp.server.fastmcp import FastMCP
    forge=from_env(); mcp=FastMCP('qdw-forge')
    @mcp.tool()
    def list_capabilities()->str:
        caps=sorted({c for a in forge.store.list_assets() if a.status.value=='ACTIVE' for c in a.capabilities})
        return json.dumps(caps)
    @mcp.tool()
    def lease_capability(capability:str,calls:int=1,ttl_seconds:int=3600,max_spend_usd:float|None=None)->str:
        lease,token=forge.leases.create(LeaseRequest(capability=capability,calls=calls,ttl_seconds=ttl_seconds,max_spend_usd=max_spend_usd))
        return json.dumps({'lease':lease.model_dump(mode='json'),'token':token},default=str)
    @mcp.tool()
    def invoke_capability(lease_token:str,capability:str,arguments_json:str,client_request_id:str)->str:
        req=InvocationRequest(lease_token=lease_token,capability=capability,arguments=json.loads(arguments_json),client_request_id=client_request_id)
        return forge.invocations.invoke(req).model_dump_json()
    return mcp

def main(): build_server().run()
if __name__=='__main__': main()
