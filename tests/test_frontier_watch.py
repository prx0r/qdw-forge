from qdw_forge.frontier_watch import FrontierWatch
from qdw_forge.models import TechniqueCandidate
class Fake:
    def search(self,q,max_results=20): return [TechniqueCandidate(technique_id='same',title='Agent harness',source_url='u',summary='routing benchmark',extension_points=['harness'])]
def test_watch_dedupes_across_queries(forge):
    s=FrontierWatch(forge.store,Fake()).scan(['a','b'],5); assert s.fetched==2 and s.stored==1 and s.unique_ids==1
