from __future__ import annotations
from dataclasses import dataclass
from .frontier import ArxivClient
from .store import ForgeStore

DEFAULT_QUERIES=(
    'cat:cs.AI AND (agent OR agentic)',
    'cat:cs.SE AND (coding agent OR software agent)',
    'all:(LLM routing OR model routing OR harness)',
    'all:(agent verification OR agent benchmark OR agent protocol)',
)

@dataclass(frozen=True)
class ScanStats:
    fetched:int; stored:int; unique_ids:int

class FrontierWatch:
    def __init__(self,store:ForgeStore,client:ArxivClient|None=None): self.store=store; self.client=client or ArxivClient()
    def scan(self,queries=DEFAULT_QUERIES,max_results_per_query:int=20)->ScanStats:
        seen=set(); fetched=0; stored=0
        for q in queries:
            for t in self.client.search(q,max_results=max_results_per_query):
                fetched+=1
                if t.technique_id in seen: continue
                seen.add(t.technique_id); self.store.save_technique(t); stored+=1
        return ScanStats(fetched,stored,len(seen))
