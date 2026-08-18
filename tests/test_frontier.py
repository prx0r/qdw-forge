from qdw_forge.frontier import parse_arxiv_atom
ATOM=b"<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'><entry><id>https://arxiv.org/abs/1</id><published>2026-08-17T00:00:00Z</published><title>Harness routing for agents</title><summary>A benchmark studies routing and context in an execution harness.</summary></entry></feed>"
def test_frontier_maps_extension_points():
    x=parse_arxiv_atom(ATOM)[0]; assert 'router' in x.extension_points; assert 'harness' in x.extension_points; assert 'benchmark' in x.extension_points
