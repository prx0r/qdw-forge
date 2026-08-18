from __future__ import annotations
from typing import Any

def validate_shallow(schema:dict[str,Any],value:Any)->list[str]:
    """Small fail-closed validator for the common JSON-schema object/required/type subset.
    It deliberately rejects unsupported schema constructs instead of pretending full JSON Schema support.
    """
    if not schema: return []
    unsupported=set(schema)-{"type","required","properties","additionalProperties"}
    if unsupported: return [f"unsupported schema keywords: {sorted(unsupported)}"]
    errs=[]
    typ=schema.get("type")
    if typ=="object":
        if not isinstance(value,dict): return ["expected object"]
        for k in schema.get("required",[]):
            if k not in value: errs.append(f"missing required field: {k}")
        props=schema.get("properties",{})
        for k,v in value.items():
            if k not in props:
                if schema.get("additionalProperties",True) is False: errs.append(f"unexpected field: {k}")
                continue
            st=props[k].get("type")
            ok={"string":isinstance(v,str),"number":isinstance(v,(int,float)) and not isinstance(v,bool),"integer":isinstance(v,int) and not isinstance(v,bool),"boolean":isinstance(v,bool),"object":isinstance(v,dict),"array":isinstance(v,list),"null":v is None}.get(st,True)
            if not ok: errs.append(f"field {k}: expected {st}")
    elif typ and typ not in {"string","number","integer","boolean","array","null"}: errs.append(f"unsupported root type: {typ}")
    return errs
