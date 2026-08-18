from __future__ import annotations
import os, secrets
from typing import Any, Protocol
import httpx
from .models import CapabilityAsset, TransportKind
from .schema_validation import validate_shallow

class Invoker(Protocol):
    def invoke(self,asset:CapabilityAsset,args:dict[str,Any])->tuple[dict[str,Any],float]: ...

class HttpInvoker:
    def __init__(self,client:httpx.Client|None=None): self.client=client or httpx.Client()
    def invoke(self,asset:CapabilityAsset,args:dict[str,Any])->tuple[dict[str,Any],float]:
        t=asset.transport; assert t is not None
        headers={"content-type":"application/json"}
        if t.auth_env:
            token=os.environ.get(t.auth_env)
            if not token: raise RuntimeError(f"missing auth env {t.auth_env}")
            headers["authorization"]="Bearer "+token
        r=self.client.post(t.endpoint,json=args,headers=headers,timeout=t.timeout_seconds); r.raise_for_status(); out=r.json()
        errs=validate_shallow(asset.output_schema,out)
        if errs: raise ValueError("output schema violation: "+"; ".join(errs))
        cost=float(r.headers.get("x-qdw-cost-usd",asset.pricing.per_call))
        return out,cost

class McpInvoker:
    def __init__(self,client:httpx.Client|None=None): self.client=client or httpx.Client()
    def invoke(self,asset:CapabilityAsset,args:dict[str,Any])->tuple[dict[str,Any],float]:
        t=asset.transport; assert t is not None and t.tool_name
        headers={"content-type":"application/json","Mcp-Method":"tools/call","Mcp-Name":t.tool_name}
        if t.auth_env:
            token=os.environ.get(t.auth_env)
            if not token: raise RuntimeError(f"missing auth env {t.auth_env}")
            headers["authorization"]="Bearer "+token
        payload={"jsonrpc":"2.0","id":secrets.token_hex(8),"method":"tools/call","params":{"name":t.tool_name,"arguments":args}}
        r=self.client.post(t.endpoint,json=payload,headers=headers,timeout=t.timeout_seconds); r.raise_for_status(); body=r.json()
        if body.get("error"): raise RuntimeError(f"MCP error: {body['error']}")
        result=body.get("result")
        if not isinstance(result,dict): result={"result":result}
        errs=validate_shallow(asset.output_schema,result)
        if errs: raise ValueError("output schema violation: "+"; ".join(errs))
        cost=float(r.headers.get("x-qdw-cost-usd",asset.pricing.per_call))
        return result,cost

class A2AInvoker:
    """Minimal A2A 1.0 JSON/HTTP client for opaque remote agents.
    The asset endpoint is the agent interface URL; results must be concrete artifacts/data.
    """
    def __init__(self,client:httpx.Client|None=None): self.client=client or httpx.Client()
    def invoke(self,asset:CapabilityAsset,args:dict[str,Any])->tuple[dict[str,Any],float]:
        t=asset.transport; assert t is not None
        headers={"content-type":"application/json","A2A-Version":"1.0"}
        if t.auth_env:
            token=os.environ.get(t.auth_env)
            if not token: raise RuntimeError(f"missing auth env {t.auth_env}")
            headers["authorization"]="Bearer "+token
        payload={"message":{"role":"user","parts":[{"data":args,"mediaType":"application/json"}]}}
        r=self.client.post(t.endpoint,json=payload,headers=headers,timeout=t.timeout_seconds); r.raise_for_status(); body=r.json()
        # A2A may return Message or Task. Forge does not pretend asynchronous Tasks are complete.
        if "status" in body and "id" in body:
            state=((body.get("status") or {}).get("state") or "").lower()
            if state not in {"completed","task_state_completed"}: raise RuntimeError(f"A2A task not terminal-complete: {state or 'unknown'}")
            artifacts=body.get("artifacts") or []
            result={"task_id":body["id"],"artifacts":artifacts}
        else:
            result=body
        errs=validate_shallow(asset.output_schema,result)
        if errs: raise ValueError("output schema violation: "+"; ".join(errs))
        cost=float(r.headers.get("x-qdw-cost-usd",asset.pricing.per_call))
        return result,cost

class Dispatcher:
    def __init__(self,http:Invoker|None=None,mcp:Invoker|None=None,a2a:Invoker|None=None): self.http=http or HttpInvoker(); self.mcp=mcp or McpInvoker(); self.a2a=a2a or A2AInvoker()
    def invoke(self,asset:CapabilityAsset,args:dict[str,Any]):
        if asset.transport is None: raise ValueError("asset has no invokable transport")
        if asset.transport.kind in {TransportKind.HTTP,TransportKind.ESTATE}: return self.http.invoke(asset,args)
        if asset.transport.kind==TransportKind.MCP: return self.mcp.invoke(asset,args)
        if asset.transport.kind==TransportKind.A2A: return self.a2a.invoke(asset,args)
        raise ValueError(f"transport {asset.transport.kind} requires a rights backend, not direct invocation")
