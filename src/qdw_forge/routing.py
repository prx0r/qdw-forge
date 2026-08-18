from __future__ import annotations
import math
from .models import CapabilityAsset, RouteCandidate, RouteDecision
from .store import ForgeStore
from .hashing import sha256_obj

class VerifiedProfileRouter:
    policy_id="verified-cpvs/v1"
    def __init__(self,store:ForgeStore): self.store=store
    def choose(self,capability:str,*,quality_floor:float|None=None,asset_id:str|None=None,version:str|None=None)->tuple[CapabilityAsset,RouteDecision]:
        assets=self.store.candidates(capability,active_only=True)
        if asset_id: assets=[a for a in assets if a.asset_id==asset_id and (version is None or a.version==version)]
        if not assets: raise LookupError("no active capability assets")
        cands=[]; qualifying=[]
        for a in assets:
            p=self.store.profile(a.asset_id,a.version,capability)
            mean=p.success_mean
            # Conservative but dependency-free lower hint; not advertised as a formal confidence bound.
            lower=max(0.0, mean - (1.0/math.sqrt(max(1,p.sample_count+2))))
            mean_cost=p.mean_cost if p.sample_count else a.pricing.per_call
            cpvs=mean_cost/max(mean,0.05)
            c=RouteCandidate(asset_id=a.asset_id,version=a.version,posterior_mean=mean,posterior_lower_hint=lower,mean_cost_usd=mean_cost,expected_cost_per_verified_success=cpvs,sample_count=p.sample_count)
            cands.append(c)
            declared=a.declared_quality if p.sample_count==0 else mean
            if quality_floor is None or (declared is not None and declared>=quality_floor): qualifying.append((a,c))
        if not qualifying: raise LookupError("no asset meets quality floor")
        qualifying.sort(key=lambda ac:(ac[1].expected_cost_per_verified_success,-ac[1].posterior_mean,-ac[1].sample_count,ac[0].asset_id,ac[0].version))
        chosen,cc=qualifying[0]
        payload={"policy":self.policy_id,"capability":capability,"chosen_asset_id":chosen.asset_id,"chosen_version":chosen.version,"candidates":[x.model_dump() for x in cands],"reason_codes":["ACTIVE_CERTIFIED_ONLY","MIN_EXPECTED_CPVS"]}
        d=RouteDecision(**payload,decision_hash=sha256_obj(payload))
        return chosen,d
