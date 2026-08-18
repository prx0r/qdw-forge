from __future__ import annotations
import base64, hashlib, hmac, json, time
from typing import Any

def b64e(b:bytes)->str: return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def b64d(s:str)->bytes: return base64.urlsafe_b64decode(s + "="*((4-len(s)%4)%4))

class LeaseTokenSigner:
    def __init__(self,secret:bytes):
        if len(secret)<32: raise ValueError("lease signing secret must be >=32 bytes")
        self.secret=secret
    def issue(self,claims:dict[str,Any])->str:
        header={"alg":"HS256","typ":"QDW-LEASE","v":1}
        h=b64e(json.dumps(header,sort_keys=True,separators=(",",":")).encode())
        p=b64e(json.dumps(claims,sort_keys=True,separators=(",",":")).encode())
        sig=b64e(hmac.new(self.secret,f"{h}.{p}".encode(),hashlib.sha256).digest())
        return f"{h}.{p}.{sig}"
    def verify(self,token:str)->dict[str,Any]:
        try: h,p,s=token.split(".")
        except ValueError as e: raise ValueError("malformed lease token") from e
        expected=b64e(hmac.new(self.secret,f"{h}.{p}".encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(expected,s): raise ValueError("invalid lease token signature")
        claims=json.loads(b64d(p))
        if float(claims.get("exp",0)) < time.time(): raise ValueError("lease token expired")
        return claims
