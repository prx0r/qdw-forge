from qdw_forge.hashing import sha256_obj, sha256_bytes, canonical_bytes

def test_sha256_obj_deterministic():
    a = sha256_obj({"key": "value", "nested": [1, 2, 3]})
    b = sha256_obj({"key": "value", "nested": [1, 2, 3]})
    assert a == b
    assert a.startswith("sha256:")

def test_sha256_obj_order_independent():
    a = sha256_obj({"b": 2, "a": 1})
    b = sha256_obj({"a": 1, "b": 2})
    assert a == b

def test_sha256_obj_different_input():
    a = sha256_obj({"x": 1})
    b = sha256_obj({"x": 2})
    assert a != b

def test_sha256_bytes():
    h = sha256_bytes(b"hello world")
    assert h.startswith("sha256:")
    assert len(h) == 71  # "sha256:" + 64 hex chars = 71

def test_canonical_bytes_sort_keys():
    result = canonical_bytes({"z": 1, "a": 2})
    assert b'"a":2' in result
    assert b'"z":1' in result
    assert result.index(b'"a"') < result.index(b'"z"')
