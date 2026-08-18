from qdw_forge.schema_validation import validate_shallow

def test_empty_schema_passes_anything():
    assert validate_shallow({}, "anything") == []
    assert validate_shallow({}, 42) == []
    assert validate_shallow({}, None) == []

def test_object_type_rejects_non_object():
    errs = validate_shallow({"type": "object"}, "not an object")
    assert errs == ["expected object"]

def test_object_required_fields():
    schema = {"type": "object", "required": ["name", "age"], "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    errs = validate_shallow(schema, {"name": "alice"})
    assert any("missing required field: age" in e for e in errs)

def test_object_additional_properties_false():
    schema = {"type": "object", "properties": {"x": {"type": "string"}}, "additionalProperties": False}
    errs = validate_shallow(schema, {"x": "ok", "extra": "bad"})
    assert any("unexpected field: extra" in e for e in errs)

def test_type_mismatch():
    schema = {"type": "object", "properties": {"count": {"type": "integer"}}}
    errs = validate_shallow(schema, {"count": "not_int"})
    assert any("expected integer" in e for e in errs)

def test_valid_object():
    schema = {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}}
    errs = validate_shallow(schema, {"text": "hello"})
    assert errs == []

def test_unsupported_keywords_rejected():
    schema = {"type": "object", "patternProperties": {".*": {"type": "string"}}}
    errs = validate_shallow(schema, {})
    assert any("unsupported" in e for e in errs)
