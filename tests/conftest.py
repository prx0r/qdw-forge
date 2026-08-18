import pytest
from qdw_forge.app import ForgeApp
@pytest.fixture
def forge(tmp_path): return ForgeApp(tmp_path/'forge.db',b'x'*32)
