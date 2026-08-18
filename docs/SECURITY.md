# Security and trust boundaries

## Executor is untrusted

Executor output can suggest artifacts, summaries and evidence references. It cannot:
- set a node to VERIFIED/SUCCEEDED;
- issue a certificate;
- update its own empirical success profile;
- mutate canonical Git directly;
- choose or weaken trusted verification gates.

## Sandbox

DockerBackend emits controls for:
- non-root UID/GID;
- `--cap-drop ALL`;
- `no-new-privileges`;
- PID, CPU, memory and wall limits;
- read-only root filesystem;
- isolated writable workspace only;
- no Docker socket or host networking;
- network none by default.

`allowlist` networking fails closed unless an external QDW egress proxy is configured. Docker alone cannot safely enforce domain-level allowlists.

ProcessBackend is explicitly development/testing only and is disabled by default in the API service. Its receipts state `isolation=NONE`.

## Secret handling

Environment values and common bearer/API/GitHub-token patterns are redacted from persisted stdout/stderr. Environment secret values are not included in environment hashes or receipts.

## Fresh verification

Production code-change verification should occur in a fresh sandbox materialized from the same base Git SHA, with the patch applied by the verifier. Trusted verifier definitions must live outside the executor-modifiable workspace or be content-hash pinned by the control plane.

## Fail closed

Unknown backend, unsupported network policy, missing repository revision, hash mismatch, zero verification gates, failing gates, illegal episode transition and unverified profile update all raise hard errors.
