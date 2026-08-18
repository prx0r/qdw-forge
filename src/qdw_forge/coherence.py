from __future__ import annotations
import ast
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class WorkingSet:
    files:tuple[str,...]
    reasons:dict[str,tuple[str,...]]

class PythonWorkingSetBuilder:
    """Conservative local coupled-fact working set: targets + local imports + nearby tests/config/policy."""
    def build(self,repo_path:str|Path,targets:list[str],max_files:int=80)->WorkingSet:
        repo=Path(repo_path).resolve(); reasons:dict[str,set[str]]={}
        def add(path:Path,reason:str):
            try: rel=str(path.resolve().relative_to(repo))
            except ValueError: return
            if path.is_file(): reasons.setdefault(rel,set()).add(reason)
        for t in targets:
            p=repo/t
            if not p.exists(): raise FileNotFoundError(t)
            add(p,'target')
            if p.suffix=='.py':
                try: tree=ast.parse(p.read_text())
                except Exception: tree=None
                if tree:
                    for n in ast.walk(tree):
                        names=[]
                        if isinstance(n,ast.Import): names=[x.name for x in n.names]
                        elif isinstance(n,ast.ImportFrom) and n.module: names=[n.module]
                        for name in names:
                            q=repo/Path(*name.split('.'))
                            for cand in (q.with_suffix('.py'),q/'__init__.py'):
                                if cand.exists(): add(cand,'local_import')
            stem=p.stem
            for cand in repo.rglob(f'test*{stem}*.py'): add(cand,'related_test')
        for name in ('AGENTS.md','qdw.yaml','pyproject.toml','package.json','Cargo.toml','Dockerfile'):
            q=repo/name
            if q.exists(): add(q,'repo_contract')
        ranked=sorted(reasons,key=lambda r:(0 if 'target' in reasons[r] else 1,0 if 'repo_contract' in reasons[r] else 1,r))[:max_files]
        return WorkingSet(tuple(ranked),{r:tuple(sorted(reasons[r])) for r in ranked})
