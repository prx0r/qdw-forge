from __future__ import annotations
import hashlib, json
from typing import Any

def canonical_bytes(value: Any) -> bytes:
    if hasattr(value, "model_dump"):
        value = value.model_dump(mode="json")
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()

def sha256_obj(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))
