from __future__ import annotations
import hashlib, json, secrets, time
from datetime import UTC, datetime, timedelta
from .db import Database
from .models import LeaseRequest, CapabilityLease
from .routing import VerifiedProfileRouter
from .tokens import LeaseTokenSigner

def now(): return datetime.now(UTC)

class LeaseService:
    def __init__(self,db:Database,router:VerifiedProfileRouter,signer:LeaseTokenSigner): self.db=db; self.router=router; self.signer=signer
    def create(self,req:LeaseRequest)->tuple[CapabilityLease,str]:
        chosen,_=self.router.choose(req.capability,quality_floor=req.quality_floor,asset_id=req.asset_id,version=req.version)
        lease_id="lease_"+secrets.token_hex(12); exp=now()+timedelta(seconds=req.ttl_seconds)
        claims={"lease_id":lease_id,"cap":req.capability,"asset":chosen.asset_id,"ver":chosen.version,"ops":req.allowed_operations,"exp":exp.timestamp(),"nonce":secrets.token_hex(8)}
        token=self.signer.issue(claims); th=hashlib.sha256(token.encode()).hexdigest()
        with self.db.tx(immediate=True) as con:
            con.execute("""INSERT INTO leases(lease_id,capability,asset_id,version,calls_total,max_spend_usd,allowed_operations_json,expires_at,status,token_hash,created_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(lease_id,req.capability,chosen.asset_id,chosen.version,req.calls,req.max_spend_usd,json.dumps(req.allowed_operations),exp.isoformat(),"ACTIVE",th,now().isoformat()))
        lease=CapabilityLease(lease_id=lease_id,capability=req.capability,asset_id=chosen.asset_id,version=chosen.version,calls_total=req.calls,max_spend_usd=req.max_spend_usd,allowed_operations=req.allowed_operations,expires_at=exp)
        return lease,token
    def verify(self,token:str,capability:str)->CapabilityLease:
        claims=self.signer.verify(token)
        if claims.get("cap")!=capability: raise PermissionError("capability outside lease")
        with self.db.connect() as con: r=con.execute("SELECT * FROM leases WHERE lease_id=?",(claims["lease_id"],)).fetchone()
        if not r or r['status']!='ACTIVE': raise PermissionError("lease inactive")
        exp=datetime.fromisoformat(r['expires_at'])
        if exp < now(): raise PermissionError("lease expired")
        return CapabilityLease(lease_id=r['lease_id'],capability=r['capability'],asset_id=r['asset_id'],version=r['version'],calls_total=r['calls_total'],calls_used=r['calls_used'],max_spend_usd=r['max_spend_usd'],spend_usd=r['spend_usd'],allowed_operations=json.loads(r['allowed_operations_json']),expires_at=exp,status=r['status'])
    def consume(self,lease_id:str,cost_usd:float):
        if cost_usd<0: raise ValueError("cost_usd must be >=0")
        with self.db.tx(immediate=True) as con:
            r=con.execute("SELECT calls_total,calls_used,max_spend_usd,spend_usd,status FROM leases WHERE lease_id=?",(lease_id,)).fetchone()
            if not r or r['status']!='ACTIVE': raise PermissionError("lease inactive")
            if r['calls_used']>=r['calls_total']: raise PermissionError("lease call limit exhausted")
            if r['max_spend_usd'] is not None and r['spend_usd']+cost_usd>r['max_spend_usd']+1e-12: raise PermissionError("lease spend limit exceeded")
            con.execute("UPDATE leases SET calls_used=calls_used+1,spend_usd=spend_usd+? WHERE lease_id=?",(cost_usd,lease_id))
