from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Metrics:
    episodes:int
    verified_success_rate:float
    cost_per_verified_success:float
    security_regressions:int=0

@dataclass(frozen=True)
class PromotionDecision:
    promote:bool
    reasons:tuple[str,...]

@dataclass(frozen=True)
class PromotionPolicy:
    min_episodes:int=100
    min_cpvs_improvement:float=0.05
    max_success_regression:float=0.01
    def evaluate(self,baseline:Metrics,candidate:Metrics)->PromotionDecision:
        reasons=[]
        if candidate.episodes<self.min_episodes: reasons.append('INSUFFICIENT_EPISODES')
        if candidate.security_regressions>0: reasons.append('SECURITY_REGRESSION')
        if candidate.verified_success_rate < baseline.verified_success_rate-self.max_success_regression: reasons.append('SUCCESS_REGRESSION')
        if baseline.cost_per_verified_success>0:
            improvement=(baseline.cost_per_verified_success-candidate.cost_per_verified_success)/baseline.cost_per_verified_success
            if improvement<self.min_cpvs_improvement: reasons.append('CPVS_IMPROVEMENT_TOO_SMALL')
        else: reasons.append('BASELINE_CPVS_UNKNOWN')
        return PromotionDecision(not reasons,tuple(reasons or ['PROMOTE']))
