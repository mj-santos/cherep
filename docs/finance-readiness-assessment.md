# Finance Pipeline Readiness Assessment (Current Repo)

> Scope note: this repository currently contains Umbrel app-store metadata (`umbrel-app-store.yml`, `cherep-wallos/umbrel-app.yml`, `docker-compose.yml`) and icons, not a transaction-processing codebase.

## 1) Architecture sanity

### Initial answer
- Current architecture is a static app-store descriptor layer:
  - `umbrel-app-store.yml` defines app-store identity.
  - `cherep-wallos/umbrel-app.yml` defines listing metadata.
  - `cherep-wallos/docker-compose.yml` defines runtime containers/volumes.
- There are no ingest/normalize/validate/analytics modules.
- There are no DuckDB tables or Parquet outputs.

### Revised answer (after weakness review)
- The previous answer is correct but incomplete for planning: there is no data-layer at all, so every finance-grade concern is currently an unimplemented requirement.
- Missing layers if this repo is meant to support finance processing:
  1. Raw input landing zone with immutable file IDs/checksums.
  2. Parse/normalize pipeline with explicit schema contracts.
  3. Validation and reconciliation layer.
  4. Storage layer (DuckDB + partitioned Parquet).
  5. Audit/run ledger and replay controller.

### Weaknesses found in my first pass
- I initially only described “what exists” but did not map a target decomposition and boundaries.

### Implementation in this change
- Added a repository validation script (`scripts/validate_manifests.py`) to enforce deterministic metadata rules where possible in the current repo.

## 2) Data correctness + auditability

### Initial answer
- Amount signs: no transaction parser exists, so no sign logic exists.
- Decimal usage: no amount type exists; therefore no Decimal/float path exists.
- Date ambiguity: no date parser exists.
- Audit trail: no run IDs, no input checksums, no row-level error logs.
- Deterministic replay: impossible because no ingest/run framework exists here.

### Revised answer
- For a future finance engine, required fail-fast controls should include:
  - Strict decimal parsing with locale-aware rules and explicit sign precedence.
  - Date format must be configured per bank; reject ambiguous inputs.
  - Full run manifest: input file hashes, parser version, mapping version, row counts at each stage.

### Weaknesses found in my first pass
- Needed to distinguish “missing today” vs “required for production”.

### Implementation in this change
- Added deterministic checks around manifest consistency (app-store ID prefix, required fields) as a first auditability baseline for this repo.

## 3) Idempotency + dedupe

### Initial answer
- No transaction ingestion exists, so idempotency/dedupe behavior is not implemented.

### Revised answer
- Proposed future fingerprint baseline:
  - Stable fields: account_id, booking_date, value_date, normalized_amount, normalized_currency, canonical_counterparty, reference.
  - Exclude mutable/derived fields (ingest timestamp, file path, parser run ID).
- Reversals/chargebacks should be represented as new events linked by reversal_reference (not deduped away).

### Weaknesses found in my first pass
- Did not specify stable-vs-unstable fields for fingerprinting.

### Implementation in this change
- N/A in runtime behavior; documented expected fingerprint properties for future work.

## 4) Performance + scalability

### Initial answer
- No data pipeline exists, so there are no measured hotspots.

### Revised answer
- Future profiling plan should capture stage timings and row counts for parse → normalize → validate → load.
- DuckDB/Parquet best-practice baseline:
  - Bulk load via DuckDB (COPY/read_csv_auto with explicit schema), avoid pandas where possible.
  - Partition Parquet by coarse date buckets.
  - Query via `read_parquet` with date predicates for pruning.

### Weaknesses found in my first pass
- Did not provide a concrete profiling plan structure.

### Implementation in this change
- N/A to runtime performance; this repo has no analytics engine.

## 5) Config + extensibility (new banks)

### Initial answer
- There is no bank mapping system in this repo.

### Revised answer
- Future extension contract should include:
  1. New mapping file + schema validation before run.
  2. Mapping semantic version pinning in run manifest.
  3. Compatibility tests against golden fixtures.

### Weaknesses found in my first pass
- Needed concrete “how-to-add” checkpoints even for planned systems.

### Implementation in this change
- Added `scripts/validate_manifests.py` as a pattern for preflight validation in this repo.

## 6) Testing quality

### Initial answer
- No parser tests or finance fixtures currently exist.

### Revised answer
- Finance-grade minimum test matrix should include localized numbers, parentheses negatives, D/C flags, empty strings, malformed quoting, and golden fixtures (CSV → normalized rows).

### Weaknesses found in my first pass
- Did not enumerate a minimum gate for release readiness.

### Implementation in this change
- Added automated repository checks and a documented command in README.

## 7) Security + privacy

### Initial answer
- Sensitive financial payloads are not present in this repo itself.
- Potential risk: using `latest` image tags reduces reproducibility and supply-chain control.

### Revised answer
- For current scope, secure-by-default actions are:
  - Validate metadata consistency on each change.
  - Warn on floating image/app versions.
  - Add guidance to pin image tags/digests.
- For future finance scope:
  - PII minimization, masked logs, encrypted-at-rest data stores, strict file path handling.

### Weaknesses found in my first pass
- Needed to separate immediate repository hardening from future finance controls.

### Implementation in this change
- Validation script now emits warnings for floating `latest` tags to flag reproducibility/supply-chain risk.
