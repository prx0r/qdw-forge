# QDW Estate V1 architecture

## Separation of powers

- `qdw`: deterministic control plane, authority over identity/state/budgets/leases/evidence/verification/outcomes.
- `qdw-sandbox`: disposable execution plane, returns receipts only.
- planners/routers/agents/humans/data providers: fallible resource providers.
- verifier: trusted policy-controlled authority; executors cannot promote themselves.

## Stable objects

1. `CapabilityRequest` — desired capability and constraints, vendor-neutral.
2. `ResourceDescriptor` — versioned candidate resource/executor configuration.
3. `WorkflowTemplate` — reusable workflow shape.
4. realized QDW `WorkGraph` — run-specific dependency graph.
5. `RouteDecision` — immutable candidate snapshot + policy version + choice.
6. `ContextPack` — policy-filtered minimum context artifact.
7. `ExecutionEpisode` — one resource attempt against one node.
8. `ExecutionReceipt` — sandbox-observed command/output/patch/environment evidence.
9. `VerificationCertificate` — trusted gate results; only authority that can produce verified success.
10. `ResourceProfile` — empirical statistics updated only from certificate-bound episodes.

## Hot path

CapabilityRequest -> candidate resources -> hard constraints -> routing policy -> RouteDecision -> ContextPack -> ExecutionEpisode -> qdw-sandbox -> ExecutionReceipt -> QDW Verification -> Certificate -> WorkGraph success -> ResourceProfile update.

## Replaceable edges

- Router: historical/cluster/cascade today; learned router tomorrow.
- Agent: Hermes/Codex/Claude/custom.
- Model gateway: current HotSwap/LiteLLM/direct providers.
- Sandbox: qdw-sandbox Docker, E2B, Kubernetes, future runtime.
- Durable backend: current QDW lease DAG, Temporal later if justified.
- Store: current SQLite, Postgres when measured scale requires it.

The Estate core must not encode assumptions about which edge implementation wins.
