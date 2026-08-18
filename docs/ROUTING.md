# Routing design

## Why simple policies ship first

Recent routing benchmarks show sophisticated routers are not uniformly superior to simple baselines. Estate therefore makes routing replaceable and records the data needed to evaluate any future policy.

## Policies in this pack

### historical-profile/v1

Ranks eligible resources by empirical cost per expected verified success. Unknown resources remain eligible for cold-start exploration but do not magically receive zero cost or perfect success.

### cluster-profile/v1

Clean-room Avengers-style mechanism:
- deterministic hashed-token vectorization;
- k-means-like centroid fitting;
- per-cluster resource success/cost statistics;
- nearest-cluster routing under Estate hard constraints.

No third-party code/model artifacts are vendored.

### cascade/v1

Uses the same empirical ordering and returns bounded fallback resources. The execution coordinator can attempt a fallback only under explicit recovery budget.

### existing QDW HotSwap

Keep current model/provider HotSwap as a sub-policy for selecting provider/model routes inside an executor configuration. It is not the Estate-wide resource router.

## Promotion

New router -> historical replay -> shadow decisions -> canary -> default only after measured improvement in cost per verified success and no verification/security regression.
