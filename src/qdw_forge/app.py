from __future__ import annotations
import os
from pathlib import Path
from .db import Database
from .store import ForgeStore
from .routing import VerifiedProfileRouter
from .leases import LeaseService
from .tokens import LeaseTokenSigner
from .invokers import Dispatcher
from .invocation import InvocationService

class ForgeApp:
    def __init__(self,db_path:str|Path,secret:bytes):
        self.db=Database(db_path); self.store=ForgeStore(self.db); self.router=VerifiedProfileRouter(self.store)
        self.signer=LeaseTokenSigner(secret); self.leases=LeaseService(self.db,self.router,self.signer)
        self.dispatcher=Dispatcher(); self.invocations=InvocationService(self.db,self.store,self.leases,self.router,self.dispatcher)

def from_env()->ForgeApp:
    secret=os.environ.get('QDW_FORGE_LEASE_SECRET','').encode()
    if len(secret)<32:
        # deterministic development-only fallback is deliberately opt-in via explicit env below
        if os.environ.get('QDW_FORGE_ALLOW_DEV_SECRET')!='1': raise RuntimeError('QDW_FORGE_LEASE_SECRET must be >=32 bytes')
        secret=b'dev-only-not-for-production-000000000000'
    return ForgeApp(os.environ.get('QDW_FORGE_DB','data/forge.db'),secret)
