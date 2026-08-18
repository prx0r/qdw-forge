import subprocess
from qdw_forge.repo2bench import HistoryTaskBuilder

def sh(cwd,*args): subprocess.run(args,cwd=cwd,check=True,text=True,capture_output=True)
def test_repo_history_builds_reversible_task(tmp_path):
    sh(tmp_path,'git','init','-q'); sh(tmp_path,'git','config','user.email','x@example.com'); sh(tmp_path,'git','config','user.name','x')
    (tmp_path/'a.txt').write_text('one\n'); sh(tmp_path,'git','add','.'); sh(tmp_path,'git','commit','-qm','base')
    (tmp_path/'a.txt').write_text('one\ntwo\n'); sh(tmp_path,'git','add','.'); sh(tmp_path,'git','commit','-qm','feature')
    t=HistoryTaskBuilder().build(tmp_path); assert t.changed_files==('a.txt',); assert t.reverse_patch_hash.startswith('sha256:'); assert '-two' in t.reverse_patch or '+two' in t.solution_patch
