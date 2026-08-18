from __future__ import annotations
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator

SCHEMA = r"""
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS assets(
  asset_id TEXT NOT NULL, version TEXT NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL,
  status TEXT NOT NULL, manifest_json TEXT NOT NULL, manifest_hash TEXT NOT NULL,
  certificate_id TEXT, created_at TEXT NOT NULL,
  PRIMARY KEY(asset_id,version)
);
CREATE TABLE IF NOT EXISTS asset_capabilities(
  asset_id TEXT NOT NULL, version TEXT NOT NULL, capability TEXT NOT NULL,
  PRIMARY KEY(asset_id,version,capability),
  FOREIGN KEY(asset_id,version) REFERENCES assets(asset_id,version) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_asset_capability ON asset_capabilities(capability);
CREATE TABLE IF NOT EXISTS leases(
  lease_id TEXT PRIMARY KEY, capability TEXT NOT NULL, asset_id TEXT, version TEXT,
  calls_total INTEGER NOT NULL, calls_used INTEGER NOT NULL DEFAULT 0,
  max_spend_usd REAL, spend_usd REAL NOT NULL DEFAULT 0,
  allowed_operations_json TEXT NOT NULL, expires_at TEXT NOT NULL, status TEXT NOT NULL,
  token_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS invocations(
  invocation_id TEXT PRIMARY KEY, client_request_id TEXT NOT NULL UNIQUE,
  lease_id TEXT NOT NULL REFERENCES leases(lease_id), capability TEXT NOT NULL,
  asset_id TEXT NOT NULL, version TEXT NOT NULL, input_hash TEXT NOT NULL,
  status TEXT NOT NULL, output_json TEXT, output_hash TEXT, cost_usd REAL NOT NULL DEFAULT 0,
  route_json TEXT, verification_certificate_id TEXT, failure TEXT,
  created_at TEXT NOT NULL, finished_at TEXT
);
CREATE TABLE IF NOT EXISTS asset_profiles(
  asset_id TEXT NOT NULL, version TEXT NOT NULL, capability TEXT NOT NULL,
  alpha REAL NOT NULL DEFAULT 1, beta REAL NOT NULL DEFAULT 1, sample_count INTEGER NOT NULL DEFAULT 0,
  total_cost_usd REAL NOT NULL DEFAULT 0, updated_at TEXT NOT NULL,
  PRIMARY KEY(asset_id,version,capability)
);
CREATE TABLE IF NOT EXISTS frontier_candidates(
  technique_id TEXT PRIMARY KEY, title TEXT NOT NULL, source_url TEXT NOT NULL,
  published_at TEXT, summary TEXT NOT NULL, extension_points_json TEXT NOT NULL,
  evidence_level TEXT NOT NULL, status TEXT NOT NULL, metadata_json TEXT NOT NULL,
  content_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS repo_bench_tasks(
  task_id TEXT PRIMARY KEY, repository TEXT NOT NULL, source_commit TEXT NOT NULL,
  healthy_revision TEXT NOT NULL, parent_revision TEXT NOT NULL,
  changed_files_json TEXT NOT NULL, reverse_patch_hash TEXT NOT NULL,
  solution_patch_hash TEXT NOT NULL, manifest_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""

class Database:
    def __init__(self,path:str|Path): self.path=str(path)
    def connect(self):
        p=Path(self.path); p.parent.mkdir(parents=True,exist_ok=True)
        con=sqlite3.connect(self.path,timeout=30,isolation_level=None)
        con.row_factory=sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON"); con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA busy_timeout=5000")
        return con
    def migrate(self):
        with self.connect() as con: con.executescript(SCHEMA)
    @contextmanager
    def tx(self, immediate:bool=False)->Iterator[sqlite3.Connection]:
        con=self.connect()
        try:
            con.execute("BEGIN IMMEDIATE" if immediate else "BEGIN"); yield con; con.commit()
        except Exception: con.rollback(); raise
        finally: con.close()
