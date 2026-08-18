from __future__ import annotations
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator
from .hashing import sha256_obj

class AssetKind(StrEnum):
    FACTORY="FACTORY"; AGENT="AGENT"; TOOL="TOOL"; SKILL="SKILL"; DATA="DATA"; HUMAN="HUMAN"; VERIFIER="VERIFIER"; SERVICE="SERVICE"
class AssetStatus(StrEnum):
    CANDIDATE="CANDIDATE"; ACTIVE="ACTIVE"; PAUSED="PAUSED"; RETIRED="RETIRED"
class TransportKind(StrEnum):
    HTTP="HTTP"; MCP="MCP"; A2A="A2A"; ESTATE="ESTATE"; VANA="VANA"
class InvocationStatus(StrEnum):
    ACCEPTED="ACCEPTED"; SUCCEEDED_UNVERIFIED="SUCCEEDED_UNVERIFIED"; FAILED="FAILED"; VERIFIED="VERIFIED"; REJECTED="REJECTED"

class RepoRef(BaseModel):
    forge: str = "git"
    repository: str
    revision: str
    manifest_path: str = "qdw.yaml"

class Pricing(BaseModel):
    currency: str = "USD"
    per_call: float = 0.0
    minimum: float = 0.0
    @field_validator("per_call", "minimum")
    @classmethod
    def nonnegative(cls,v):
        if v < 0: raise ValueError("pricing must be nonnegative")
        return v

class TransportSpec(BaseModel):
    kind: TransportKind
    endpoint: str
    tool_name: str | None = None
    timeout_seconds: int = 300
    auth_env: str | None = None
    @model_validator(mode="after")
    def valid(self):
        if self.kind == TransportKind.MCP and not self.tool_name:
            raise ValueError("MCP transport requires tool_name")
        if self.timeout_seconds <= 0: raise ValueError("timeout_seconds must be > 0")
        return self

class DataRightsHandle(BaseModel):
    backend: str
    handle: str
    scopes: list[str] = Field(default_factory=list)
    operations: list[str] = Field(default_factory=lambda:["read"])
    raw_export: bool = False
    expires_at: datetime | None = None

class CapabilityAsset(BaseModel):
    asset_id: str
    version: str
    kind: AssetKind
    name: str
    capabilities: list[str]
    transport: TransportSpec | None = None
    repository: RepoRef | None = None
    pricing: Pricing = Field(default_factory=Pricing)
    declared_quality: float | None = None
    certificate_id: str | None = None
    status: AssetStatus = AssetStatus.CANDIDATE
    rights: DataRightsHandle | None = None
    input_schema: dict[str,Any] = Field(default_factory=dict)
    output_schema: dict[str,Any] = Field(default_factory=dict)
    metadata: dict[str,Any] = Field(default_factory=dict)

    @field_validator("capabilities")
    @classmethod
    def capabilities_nonempty(cls,v):
        if not v or any(not x.strip() for x in v): raise ValueError("capabilities must be nonempty")
        return sorted(set(v))
    @field_validator("declared_quality")
    @classmethod
    def quality(cls,v):
        if v is not None and not 0 <= v <= 1: raise ValueError("declared_quality outside [0,1]")
        return v
    @model_validator(mode="after")
    def active_has_certificate(self):
        if self.status == AssetStatus.ACTIVE and not self.certificate_id:
            raise ValueError("ACTIVE asset requires certificate_id")
        if self.kind == AssetKind.DATA and not self.rights:
            raise ValueError("DATA asset requires rights handle")
        if self.kind != AssetKind.DATA and self.transport is None:
            raise ValueError("non-DATA asset requires transport")
        return self
    @property
    def manifest_hash(self): return sha256_obj(self)

class FactoryCapsule(CapabilityAsset):
    kind: AssetKind = AssetKind.FACTORY
    workflow_template: str
    verification_policy: str
    harness_recipe: str | None = None

class LeaseRequest(BaseModel):
    capability: str
    asset_id: str | None = None
    version: str | None = None
    calls: int = 1
    max_spend_usd: float | None = None
    ttl_seconds: int = 3600
    allowed_operations: list[str] = Field(default_factory=lambda:["invoke"])
    quality_floor: float | None = None
    @model_validator(mode="after")
    def validate_request(self):
        if self.calls <= 0: raise ValueError("calls must be > 0")
        if self.ttl_seconds <= 0: raise ValueError("ttl_seconds must be > 0")
        if self.max_spend_usd is not None and self.max_spend_usd < 0: raise ValueError("max_spend_usd must be >= 0")
        if self.quality_floor is not None and not 0 <= self.quality_floor <= 1: raise ValueError("quality_floor outside [0,1]")
        if self.version and not self.asset_id: raise ValueError("version requires asset_id")
        return self

class CapabilityLease(BaseModel):
    lease_id: str
    capability: str
    asset_id: str | None = None
    version: str | None = None
    calls_total: int
    calls_used: int = 0
    max_spend_usd: float | None = None
    spend_usd: float = 0.0
    allowed_operations: list[str]
    expires_at: datetime
    status: str = "ACTIVE"

class InvocationRequest(BaseModel):
    lease_token: str
    capability: str
    arguments: dict[str,Any]
    client_request_id: str

class RouteCandidate(BaseModel):
    asset_id: str
    version: str
    posterior_mean: float
    posterior_lower_hint: float
    mean_cost_usd: float
    expected_cost_per_verified_success: float
    sample_count: int

class RouteDecision(BaseModel):
    policy: str
    capability: str
    chosen_asset_id: str
    chosen_version: str
    candidates: list[RouteCandidate]
    reason_codes: list[str]
    decision_hash: str

class InvocationRecord(BaseModel):
    invocation_id: str
    client_request_id: str
    lease_id: str
    capability: str
    asset_id: str
    version: str
    input_hash: str
    status: InvocationStatus
    output: dict[str,Any] | None = None
    output_hash: str | None = None
    cost_usd: float = 0.0
    route_decision: RouteDecision | None = None
    verification_certificate_id: str | None = None
    failure: str | None = None
    created_at: datetime = Field(default_factory=lambda:datetime.now(UTC))
    finished_at: datetime | None = None

class AssetProfile(BaseModel):
    asset_id: str
    version: str
    capability: str
    alpha: float = 1.0
    beta: float = 1.0
    sample_count: int = 0
    total_cost_usd: float = 0.0
    @property
    def success_mean(self): return self.alpha/(self.alpha+self.beta)
    @property
    def mean_cost(self): return self.total_cost_usd/self.sample_count if self.sample_count else 0.0

class TechniqueCandidate(BaseModel):
    technique_id: str
    title: str
    source_url: str
    published_at: datetime | None = None
    summary: str
    extension_points: list[str]
    evidence_level: str = "PAPER_CLAIM"
    status: str = "DISCOVERED"
    metadata: dict[str,Any] = Field(default_factory=dict)
