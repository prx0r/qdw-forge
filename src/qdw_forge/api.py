from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .app import from_env
from .models import CapabilityAsset,LeaseRequest,InvocationRequest

app=FastAPI(title='QDW Forge',version='0.1.0')
_state=None

def state():
    global _state
    if _state is None: _state=from_env()
    return _state

class ActivateBody(BaseModel): certificate_id:str
class VerifyBody(BaseModel): certificate_id:str; passed:bool

@app.get('/health')
def health(): return {'status':'ok'}
@app.post('/v1/assets')
def register(asset:CapabilityAsset):
    try: return state().store.register_asset(asset).model_dump(mode='json')
    except ValueError as e: raise HTTPException(409,str(e))
@app.get('/v1/assets')
def assets(capability:str|None=None):
    xs=state().store.candidates(capability,active_only=False) if capability else state().store.list_assets()
    return [x.model_dump(mode='json') for x in xs]
@app.post('/v1/assets/{asset_id}/{version}/activate')
def activate(asset_id:str,version:str,body:ActivateBody):
    try: return state().store.activate(asset_id,version,body.certificate_id).model_dump(mode='json')
    except KeyError: raise HTTPException(404,'asset not found')
@app.post('/v1/leases')
def lease(req:LeaseRequest):
    try:
        l,t=state().leases.create(req); return {'lease':l.model_dump(mode='json'),'token':t}
    except LookupError as e: raise HTTPException(404,str(e))
@app.post('/v1/invoke')
def invoke(req:InvocationRequest): return state().invocations.invoke(req).model_dump(mode='json')
@app.get('/v1/invocations/{invocation_id}')
def invocation(invocation_id:str):
    try: return state().invocations.get(invocation_id).model_dump(mode='json')
    except KeyError: raise HTTPException(404,'invocation not found')
@app.post('/v1/invocations/{invocation_id}/verification')
def verify(invocation_id:str,body:VerifyBody):
    try: state().invocations.bind_verification(invocation_id,certificate_id=body.certificate_id,passed=body.passed); return state().invocations.get(invocation_id).model_dump(mode='json')
    except KeyError: raise HTTPException(404,'invocation not found')
