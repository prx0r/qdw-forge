from __future__ import annotations
import json
from datetime import UTC, datetime
from .db import Database
from .models import CapabilityAsset, AssetStatus, AssetProfile, TechniqueCandidate
from .hashing import sha256_obj

def now(): return datetime.now(UTC).isoformat()

class ForgeStore:
    def __init__(self,db:Database): self.db=db; self.db.migrate()
    def register_asset(self,asset:CapabilityAsset)->CapabilityAsset:
        raw=asset.model_dump_json(); h=asset.manifest_hash
        with self.db.tx(immediate=True) as con:
            old=con.execute("SELECT manifest_hash FROM assets WHERE asset_id=? AND version=?",(asset.asset_id,asset.version)).fetchone()
            if old:
                if old["manifest_hash"] != h: raise ValueError("immutable asset version conflict")
                return self.get_asset(asset.asset_id,asset.version)
            con.execute("INSERT INTO assets(asset_id,version,kind,name,status,manifest_json,manifest_hash,certificate_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                        (asset.asset_id,asset.version,asset.kind.value,asset.name,asset.status.value,raw,h,asset.certificate_id,now()))
            for cap in asset.capabilities:
                con.execute("INSERT INTO asset_capabilities(asset_id,version,capability) VALUES(?,?,?)",(asset.asset_id,asset.version,cap))
        return asset
    def get_asset(self,asset_id:str,version:str)->CapabilityAsset:
        with self.db.connect() as con:
            r=con.execute("SELECT manifest_json FROM assets WHERE asset_id=? AND version=?",(asset_id,version)).fetchone()
        if not r: raise KeyError(f"{asset_id}@{version}")
        return CapabilityAsset.model_validate_json(r["manifest_json"])
    def activate(self,asset_id:str,version:str,certificate_id:str)->CapabilityAsset:
        if not certificate_id.strip(): raise ValueError("certificate_id required")
        with self.db.tx(immediate=True) as con:
            r=con.execute("SELECT manifest_json FROM assets WHERE asset_id=? AND version=?",(asset_id,version)).fetchone()
            if not r: raise KeyError(f"{asset_id}@{version}")
            asset=CapabilityAsset.model_validate_json(r["manifest_json"])
            asset=asset.model_copy(update={"status":AssetStatus.ACTIVE,"certificate_id":certificate_id})
            raw=asset.model_dump_json(); h=asset.manifest_hash
            con.execute("UPDATE assets SET status='ACTIVE',certificate_id=?,manifest_json=?,manifest_hash=? WHERE asset_id=? AND version=?",
                        (certificate_id,raw,h,asset_id,version))
        return asset
    def candidates(self,capability:str,active_only:bool=True)->list[CapabilityAsset]:
        sql="""SELECT a.manifest_json FROM assets a JOIN asset_capabilities c ON c.asset_id=a.asset_id AND c.version=a.version
               WHERE c.capability=?""" + (" AND a.status='ACTIVE'" if active_only else "") + " ORDER BY a.asset_id,a.version"
        with self.db.connect() as con: rows=con.execute(sql,(capability,)).fetchall()
        return [CapabilityAsset.model_validate_json(r["manifest_json"]) for r in rows]
    def list_assets(self)->list[CapabilityAsset]:
        with self.db.connect() as con: rows=con.execute("SELECT manifest_json FROM assets ORDER BY asset_id,version").fetchall()
        return [CapabilityAsset.model_validate_json(r["manifest_json"]) for r in rows]
    def profile(self,asset_id:str,version:str,capability:str)->AssetProfile:
        with self.db.connect() as con:
            r=con.execute("SELECT * FROM asset_profiles WHERE asset_id=? AND version=? AND capability=?",(asset_id,version,capability)).fetchone()
        if not r: return AssetProfile(asset_id=asset_id,version=version,capability=capability)
        return AssetProfile(asset_id=asset_id,version=version,capability=capability,alpha=r['alpha'],beta=r['beta'],sample_count=r['sample_count'],total_cost_usd=r['total_cost_usd'])
    def record_verified(self,asset_id:str,version:str,capability:str,*,success:bool,cost_usd:float,certificate_id:str):
        if not certificate_id.strip(): raise ValueError("verified profile update requires certificate_id")
        if cost_usd < 0: raise ValueError("cost_usd must be >=0")
        with self.db.tx(immediate=True) as con:
            con.execute("INSERT OR IGNORE INTO asset_profiles(asset_id,version,capability,updated_at) VALUES(?,?,?,?)",(asset_id,version,capability,now()))
            con.execute("""UPDATE asset_profiles SET alpha=alpha+?, beta=beta+?, sample_count=sample_count+1,
                         total_cost_usd=total_cost_usd+?, updated_at=? WHERE asset_id=? AND version=? AND capability=?""",
                        (1 if success else 0,0 if success else 1,cost_usd,now(),asset_id,version,capability))
    def save_technique(self,t:TechniqueCandidate):
        raw=t.model_dump(mode='json'); h=sha256_obj(raw)
        with self.db.tx(immediate=True) as con:
            con.execute("""INSERT OR IGNORE INTO frontier_candidates(technique_id,title,source_url,published_at,summary,extension_points_json,evidence_level,status,metadata_json,content_hash,created_at)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?)""",(t.technique_id,t.title,t.source_url,t.published_at.isoformat() if t.published_at else None,t.summary,json.dumps(t.extension_points),t.evidence_level,t.status,json.dumps(t.metadata,sort_keys=True),h,now()))
