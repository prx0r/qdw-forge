# Verification strategy

## Deterministic tests shipped

Control plane:
- deterministic contract hashing;
- constraint validation;
- immutable versioned resource descriptors;
- historical routing economics;
- deterministic cluster fit;
- sensitive context exclusion;
- zero/failing verification gates rejected;
- unverified episode cannot poison resource profile;
- certificate-bound episode can update profile.

Sandbox:
- local Git materialization at exact revision;
- bounded command execution;
- binary Git patch receipt;
- timeout is failure;
- process backend disabled by default;
- Docker command contains required hardening flags;
- allowlist network fails closed without egress proxy;
- secret redaction;
- API advertises execution-only authority.

## Mandatory tests when integrated into live QDW

- entire pre-Estate QDW suite unchanged or stronger;
- concurrent claims/heartbeats/expired leases;
- stale worker submission rejection;
- forged executor certificate rejection;
- verifier fresh-workspace patch application;
- canonical Git publish only after certificate;
- context access policy over real private objects;
- full CapabilityRequest -> route -> sandbox -> verify -> profile E2E.

## Live gates

Docker, Hermes/provider, remote private Git access and external egress are environment-dependent live gates. Missing prerequisites are `BLOCKED`, never skipped-as-pass.
