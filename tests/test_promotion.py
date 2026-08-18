from qdw_forge.promotion import Metrics,PromotionPolicy

def test_promotion_requires_evidence_and_no_security_regression():
    p=PromotionPolicy(min_episodes=100,min_cpvs_improvement=.05,max_success_regression=.01)
    base=Metrics(200,.9,1.0,0)
    assert p.evaluate(base,Metrics(120,.9,.8,0)).promote
    assert not p.evaluate(base,Metrics(20,.95,.5,0)).promote
    assert not p.evaluate(base,Metrics(120,.95,.5,1)).promote
