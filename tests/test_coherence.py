from qdw_forge.coherence import PythonWorkingSetBuilder

def test_working_set_includes_local_import_test_and_contract(tmp_path):
    (tmp_path/'pkg').mkdir(); (tmp_path/'tests').mkdir();
    (tmp_path/'pkg'/'a.py').write_text('import pkg.b\n'); (tmp_path/'pkg'/'b.py').write_text('X=1\n'); (tmp_path/'tests'/'test_a.py').write_text('pass\n'); (tmp_path/'AGENTS.md').write_text('rules')
    ws=PythonWorkingSetBuilder().build(tmp_path,['pkg/a.py']);
    assert 'pkg/a.py' in ws.files and 'pkg/b.py' in ws.files and 'AGENTS.md' in ws.files
