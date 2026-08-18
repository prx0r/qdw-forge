from __future__ import annotations
import hashlib, json, shutil, subprocess, tempfile
from dataclasses import dataclass, asdict
from datetime import UTC, datetime
from pathlib import Path
from .hashing import sha256_bytes, sha256_obj

@dataclass(frozen=True)
class RepoBenchTask:
    task_id:str; repository:str; source_commit:str; healthy_revision:str; parent_revision:str
    changed_files:tuple[str,...]; reverse_patch:str; reverse_patch_hash:str; solution_patch:str; solution_patch_hash:str
    created_at:str
    @property
    def manifest_hash(self): return sha256_obj(asdict(self))

def run(repo:Path,*args:str)->str:
    p=subprocess.run(['git','-C',str(repo),*args],text=True,capture_output=True,timeout=30)
    if p.returncode!=0: raise RuntimeError(p.stderr.strip() or 'git command failed')
    return p.stdout

class HistoryTaskBuilder:
    def build(self,repo_path:str|Path,commit:str='HEAD')->RepoBenchTask:
        repo=Path(repo_path).resolve()
        sha=run(repo,'rev-parse',commit).strip(); parent=run(repo,'rev-parse',sha+'^').strip()
        patch=run(repo,'diff','--binary',parent,sha)
        if not patch.strip(): raise ValueError('commit has no diff')
        files=tuple(x for x in run(repo,'diff','--name-only',parent,sha).splitlines() if x)
        reverse=self._reverse_patch(repo,sha,patch)
        rid=hashlib.sha256((str(repo)+sha).encode()).hexdigest()[:20]
        return RepoBenchTask(task_id='rbt_'+rid,repository=str(repo),source_commit=sha,healthy_revision=sha,parent_revision=parent,changed_files=files,reverse_patch=reverse,reverse_patch_hash=sha256_bytes(reverse.encode()),solution_patch=patch,solution_patch_hash=sha256_bytes(patch.encode()),created_at=datetime.now(UTC).isoformat())
    def _reverse_patch(self,repo:Path,healthy:str,solution_patch:str)->str:
        td=Path(tempfile.mkdtemp(prefix='qdw-r2b-')); wt=td/'wt'
        try:
            run(repo,'worktree','add','--detach',str(wt),healthy)
            p=subprocess.run(['git','-C',str(wt),'apply','--reverse','--binary','-'],input=solution_patch,text=True,capture_output=True,timeout=30)
            if p.returncode!=0: raise RuntimeError('patch reversal failed: '+p.stderr.strip())
            reverse=run(wt,'diff','--binary')
            if not reverse.strip(): raise RuntimeError('reverse patch produced no task state')
            return reverse
        finally:
            try: run(repo,'worktree','remove','--force',str(wt))
            except Exception: pass
            shutil.rmtree(td,ignore_errors=True)
