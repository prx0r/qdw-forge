# qdw-forge

Private agent-native forge above Git/Forgejo.

Core objects:

- `CapabilityAsset`: any routable machine-readable capability provider.
- `FactoryCapsule`: verified autonomous-work package referencing exact source revision and contracts.
- `CapabilityLease`: scoped, expiring right to invoke an asset/capability under call/spend limits.
- `Invocation`: immutable request/outcome record; initially unverified.
- `AssetProfile`: empirical Beta success posterior + cost history updated only from certified invocations.
- `DataRightsHandle`: opaque scoped permission reference; Vana can back it without copying raw data into Forge.
- `TechniqueCandidate`: frontier research finding mapped to a replaceable Estate extension point.
- `RepoBenchTask`: executable benchmark candidate reconstructed from repository history using patch reversal.

The forge uses its own SQLite database for local operation. QDW Estate treats it as a capability/resource provider over HTTP, keeping trust domains clean.
