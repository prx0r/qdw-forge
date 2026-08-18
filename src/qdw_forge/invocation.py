from __future__ import annotations
import json, secrets
from datetime import UTC, datetime
from .db import Database
from .hashing import sha256_obj
from .leases import LeaseService
from .models import InvocationRequest,InvocationRecord,InvocationStatus,RouteDecision
from .routing import VerifiedProfileRouter
from .store import ForgeStore
from .invokers import Dispatcher

def now(): return datetime.now(UTC)

class InvocationService:
    def __init__(self,db:Database,store:ForgeStore,leases:LeaseService,router:VerifiedProfileRouter,dispatcher:Dispatcher):
        self.db=db; self.store=store; self.leases=leases; self.router=router; self.dispatcher=dispatcher
    def invoke(self,req:InvocationRequest)->InvocationRecord:
        with self.db.connect() as con:
            old=con.execute("SELECT * FROM invocations WHERE client_request_id=?",(req.client_request_id,)).fetchone()
        if old: return self._row(old)
        lease=self.leases.verify(req.lease_token,req.capability)
        asset,decision=self.router.choose(req.capability,asset_id=lease.asset_id,version=lease.version)
        errs=[]
        from .schema_validation import validate_shallow
        errs=validate_shallow(asset.input_schema,req.arguments)
        if errs: raise ValueError("input schema violation: "+"; ".join(errs))
        invocation_id="inv_"+secrets.token_hex(12); created=now(); ih=sha256_obj(req.arguments)
        est_cost=asset.pricing.per_call
        self.leases.consume(lease.lease_id,est_cost)
        with self.db.tx(immediate=True) as con:
            con.execute("""INSERT INTO invocations(invocation_id,client_request_id,lease_id,capability,asset_id,version,input_hash,status,cost_usd,route_json,created_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(invocation_id,req.client_request_id,lease.lease_id,req.capability,asset.asset_id,asset.version,ih,InvocationStatus.ACCEPTED.value,est_cost,decision.model_dump_json(),created.isoformat()))
        try:
            output,cost=self.dispatcher.invoke(asset,req.arguments); oh=sha256_obj(output); finished=now()
            with self.db.tx(immediate=True) as con:
                con.execute("UPDATE invocations SET status=?,output_json=?,output_hash=?,cost_usd=?,finished_at=? WHERE invocation_id=?",
                            (InvocationStatus.SUCCEEDED_UNVERIFIED.value,json.dumps(output,sort_keys=True),oh,cost,finished.isoformat(),invocation_id))
            return InvocationRecord(invocation_id=invocation_id,client_request_id=req.client_request_id,lease_id=lease.lease_id,capability=req.capability,asset_id=asset.asset_id,version=asset.version,input_hash=ih,status=InvocationStatus.SUCCEEDED_UNVERIFIED,output=output,output_hash=oh,cost_usd=cost,route_decision=decision,created_at=created,finished_at=finished)
        except Exception as exc:
            finished=now()
            with self.db.tx(immediate=True) as con:
                con.execute("UPDATE invocations SET status=?,failure=?,finished_at=? WHERE invocation_id=?",(InvocationStatus.FAILED.value,str(exc),finished.isoformat(),invocation_id))
            return InvocationRecord(invocation_id=invocation_id,client_request_id=req.client_request_id,lease_id=lease.lease_id,capability=req.capability,asset_id=asset.asset_id,version=asset.version,input_hash=ih,status=InvocationStatus.FAILED,cost_usd=est_cost,route_decision=decision,failure=str(exc),created_at=created,finished_at=finished)
    def bind_verification(self,invocation_id:str,*,certificate_id:str,passed:bool):
        if not certificate_id.strip(): raise ValueError("certificate_id required")
        with self.db.tx(immediate=True) as con:
            r=con.execute("SELECT asset_id,version,capability,cost_usd,status FROM invocations WHERE invocation_id=?",(invocation_id,)).fetchone()
            if not r: raise KeyError(invocation_id)
            if r['status'] not in {InvocationStatus.SUCCEEDED_UNVERIFIED.value,InvocationStatus.FAILED.value}: raise ValueError("invocation not awaiting verification")
            status=InvocationStatus.VERIFIED.value if passed else InvocationStatus.REJECTED.value
            con.execute("UPDATE invocations SET status=?,verification_certificate_id=? WHERE invocation_id=?",(status,certificate_id,invocation_id))
        self.store.record_verified(r['asset_id'],r['version'],r['capability'],success=passed,cost_usd=float(r['cost_usd']),certificate_id=certificate_id)
    def get(self,invocation_id:str)->InvocationRecord:
        with self.db.connect() as con: r=con.execute("SELECT * FROM invocations WHERE invocation_id=?",(invocation_id,)).fetchone()
        if not r: raise KeyError(invocation_id)
        return self._row(r)
    def _row(self,r):
        return InvocationRecord(invocation_id=r['invocation_id'],client_request_id=r['client_request_id'],lease_id=r['lease_id'],capability=r['capability'],asset_id=r['asset_id'],version=r['version'],input_hash=r['input_hash'],status=InvocationStatus(r['status']),output=json.loads(r['output_json']) if r['output_json'] else None,output_hash=r['output_hash'],cost_usd=r['cost_usd'],route_decision=RouteDecision.model_validate_json(r['route_json']) if r['route_json'] else None,verification_certificate_id=r['verification_certificate_id'],failure=r['failure'],created_at=datetime.fromisoformat(r['created_at']),finished_at=datetime.fromisoformat(r['finished_at']) if r['finished_at'] else None)
