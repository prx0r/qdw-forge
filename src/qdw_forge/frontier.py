from __future__ import annotations
import hashlib, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime
import httpx
from .models import TechniqueCandidate

NS={'a':'http://www.w3.org/2005/Atom'}
MAP={
 'router':['router','routing','cascade','model selection'],
 'harness':['harness','agent runtime','orchestration'],
 'context':['context','working set','coherence','memory'],
 'verification':['verification','verifier','audit','safety'],
 'workflow':['workflow','control-flow','task graph','dag'],
 'sandbox':['sandbox','container','isolation','execution environment'],
 'benchmark':['benchmark','evaluation','task construction'],
 'protocol':['protocol','interoperability','mcp','a2a'],
 'market':['marketplace','market','allocation','auction','human-in-the-loop'],
}

def extension_points(text:str)->list[str]:
    low=text.lower(); return sorted(k for k,words in MAP.items() if any(w in low for w in words)) or ['research']

def parse_arxiv_atom(xml:bytes)->list[TechniqueCandidate]:
    root=ET.fromstring(xml); out=[]
    for e in root.findall('a:entry',NS):
        title=' '.join((e.findtext('a:title','',NS)).split()); summary=' '.join((e.findtext('a:summary','',NS)).split()); url=e.findtext('a:id','',NS)
        pub=e.findtext('a:published','',NS); dt=datetime.fromisoformat(pub.replace('Z','+00:00')) if pub else None
        tid='tech_'+hashlib.sha256(url.encode()).hexdigest()[:20]
        out.append(TechniqueCandidate(technique_id=tid,title=title,source_url=url,published_at=dt,summary=summary,extension_points=extension_points(title+' '+summary)))
    return out

class ArxivClient:
    def __init__(self,client:httpx.Client|None=None): self.client=client or httpx.Client()
    def search(self,query:str,max_results:int=25)->list[TechniqueCandidate]:
        if not 1<=max_results<=100: raise ValueError('max_results must be 1..100')
        params={'search_query':query,'start':0,'max_results':max_results,'sortBy':'submittedDate','sortOrder':'descending'}
        r=self.client.get('https://export.arxiv.org/api/query',params=params,timeout=30); r.raise_for_status(); return parse_arxiv_atom(r.content)
