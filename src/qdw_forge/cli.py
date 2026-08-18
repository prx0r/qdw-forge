from __future__ import annotations
import argparse, json, os
from pathlib import Path
from .app import ForgeApp
from .models import CapabilityAsset,LeaseRequest
from .frontier import parse_arxiv_atom
from .repo2bench import HistoryTaskBuilder

def app(db):
    secret=os.environ.get('QDW_FORGE_LEASE_SECRET','dev-only-not-for-production-000000000000').encode()
    return ForgeApp(db,secret)

def main():
    p=argparse.ArgumentParser(prog='qdw-forge'); p.add_argument('--db',default='data/forge.db'); sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('init-db')
    r=sub.add_parser('register'); r.add_argument('manifest')
    sub.add_parser('assets')
    l=sub.add_parser('lease'); l.add_argument('capability'); l.add_argument('--calls',type=int,default=1)
    a=sub.add_parser('parse-arxiv'); a.add_argument('atom_xml')
    b=sub.add_parser('repo2bench'); b.add_argument('repo'); b.add_argument('--commit',default='HEAD')
    ns=p.parse_args(); f=app(ns.db)
    if ns.cmd=='init-db': print(json.dumps({'db':ns.db,'status':'ok'}))
    elif ns.cmd=='register': print(f.store.register_asset(CapabilityAsset.model_validate_json(Path(ns.manifest).read_text())).model_dump_json(indent=2))
    elif ns.cmd=='assets': print(json.dumps([x.model_dump(mode='json') for x in f.store.list_assets()],indent=2,default=str))
    elif ns.cmd=='lease':
        lease,token=f.leases.create(LeaseRequest(capability=ns.capability,calls=ns.calls)); print(json.dumps({'lease':lease.model_dump(mode='json'),'token':token},indent=2,default=str))
    elif ns.cmd=='parse-arxiv': print(json.dumps([x.model_dump(mode='json') for x in parse_arxiv_atom(Path(ns.atom_xml).read_bytes())],indent=2,default=str))
    elif ns.cmd=='repo2bench': print(json.dumps(HistoryTaskBuilder().build(ns.repo,ns.commit).__dict__,indent=2))
if __name__=='__main__': main()
