import pytest
from datetime import UTC,datetime,timedelta
from qdw_forge.models import DataRightsHandle
from qdw_forge.vana import assert_rights

def test_vana_scope_fails_closed():
    h=DataRightsHandle(backend='vana',handle='grant1',scopes=['lifegit.problems'],operations=['read'],raw_export=False)
    assert_rights(h,scope='lifegit.problems')
    with pytest.raises(PermissionError): assert_rights(h,scope='lifegit.messages')
    with pytest.raises(PermissionError): assert_rights(h,scope='lifegit.problems',operation='raw_export')
