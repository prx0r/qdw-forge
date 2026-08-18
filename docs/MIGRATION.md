# Integration migration

## Baseline

Pack was designed against `prx0r/qdw` main observed at commit `ab809c8e6b829374199eb49dc71cd6f499e4f7fb` and an effectively empty `prx0r/qdw-sandbox` repository.

## Additive first

`apply_to_qdw.py` never overwrites an existing QDW file. It copies:
- `src/qdw/estate/**`;
- `migrations/0005_estate_core.sql`;
- Estate tests;
- manifests.

It refuses a migration-0005 collision and records baseline blob warnings.

## Composition wiring second

After all additive tests pass, make one reviewed edit to `QDWSystem`:

```python
from qdw.estate.integration import EstateServices
...
self.estate = EstateServices(self)
```

No duplicate database/ledger/work graph is created.

## Hermes third

Move direct host `subprocess.run` behind sandbox adapter only after sandbox process tests and live Docker gate are recorded.

## Storage/orchestrator upgrades later

Do not combine Estate rollout with Postgres/Temporal/Kubernetes/Jujutsu migration. Add adapter interfaces and migrate only after measured need.
