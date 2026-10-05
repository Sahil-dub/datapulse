# 3H.5.6.1 — Ingestion Orchestration Contract

## Status

**Defined — 3H.5.6.1**

This document defines the contract for the application-level ingestion orchestration workflow that will connect the existing CSV reader, CSV schema validation, raw database loader, and ingestion metadata lifecycle.

This is a contract only. The orchestration implementation is part of **3H.5.6.2+**.

## Purpose

The ingestion orchestration layer coordinates one source-file ingestion operation and ensures that operational metadata accurately describes what happened.

The workflow must connect:

```
source file
    │
    ▼
create ingestion run
    │
    ▼
create ingestion source
    │
    ▼
read CSV
    │
    ▼
validate source schema
    │
    ▼
load raw table
    │
    ├── success ──► source SUCCESS ──► run SUCCESS
    │
    └── failure ──► source FAILED  ──► run FAILED
```

The orchestration layer does not perform business transformations. Its responsibility is to coordinate ingestion and record operational state.

## Scope

### In scope

- one source file per orchestration operation
- ingestion run creation
- ingestion source creation
- CSV file reading
- source schema validation
- raw-table loading
- row-count tracking
- source lifecycle updates
- run lifecycle updates
- failure capture
- deterministic orchestration result

### Out of scope

- staging transformations
- business rules
- data-quality rules beyond source-schema validation
- anomaly detection
- retry scheduling
- parallel ingestion
- workflow scheduling
- external orchestration platforms
- API exposure

Those concerns belong to later milestones/phases.

## Input Contract

A single-source ingestion operation requires:

| Input | Type | Required | Contract |
|---|---|---:|---|
| `engine` | SQLAlchemy `Engine` | Yes | Active DataPulse PostgreSQL connection |
| `source_name` | string | Yes | Must identify one supported source |
| `source_file_path` | `Path` | Yes | Path to the source CSV |
| `batch_size` | positive integer | No | Controls raw loading batch size; default may be defined by implementation |

The `source_name` must correspond to an existing DataPulse source definition and raw-table mapping.

The source file path is recorded as supplied to the orchestration layer. The filename is derived from the path for ingestion metadata.

## Source-to-Table Mapping

The orchestration layer must use the existing source mapping rather than constructing table names dynamically from untrusted input.

Current supported sources:

| Source | Raw table |
|---|---|
| `customers` | `raw.customers` |
| `products` | `raw.products` |
| `orders` | `raw.orders` |
| `payments` | `raw.payments` |
| `subscriptions` | `raw.subscriptions` |
| `support_tickets` | `raw.support_tickets` |
| `web_events` | `raw.web_events` |

## Metadata Creation Contract

The orchestration must create metadata records **before attempting to read the source file**.

This guarantees that operational failures such as missing files are observable.

### Ingestion run

A new `metadata.ingestion_runs` record is created in:

```
status = RUNNING
```

Initial values:

- `source_name` = requested source
- `started_at` = orchestration start time
- `finished_at` = NULL
- `rows_read` = 0
- `rows_loaded` = 0
- `error_message` = NULL

### Ingestion source

A new `metadata.ingestion_sources` record is created in:

```
source_status = PENDING
```

Initial values:

- `ingestion_run_id` = parent run ID
- `source_name` = requested source
- `source_file_name` = source file name
- `source_file_path` = supplied source path
- `started_at` = orchestration/source start time
- `finished_at` = NULL
- `rows_read` = 0
- `rows_loaded` = 0
- `error_message` = NULL

## Processing Contract

The orchestration must execute these stages in order:

### 1. Register the run

Create the parent ingestion run in `RUNNING`.

### 2. Register the source

Create the child ingestion source in `PENDING`.

### 3. Read the CSV

Use the existing CSV file reader.

The reader must preserve source values as strings so invalid source values remain observable to downstream validation and data-quality processing.

### 4. Validate the source schema

Use the existing source-schema validation contract.

The orchestration must not load data into the raw table when schema validation fails.

### 5. Load the raw table

Use the existing raw database loader.

The loader's single-transaction behavior must be preserved. If a database error occurs during batch loading, all batches from that raw load operation are rolled back.

### 6. Record success

After the raw transaction commits:

- source becomes `SUCCESS`
- run becomes `SUCCESS`
- `finished_at` is populated
- `error_message` is NULL
- row counts are recorded

## Row-Count Contract

### rows_read

`rows_read` means the number of data rows successfully parsed from the CSV after reading.

The CSV header is not counted.

For the current raw ingestion contract, no filtering or transformation occurs between CSV reading and raw loading.

Therefore, on successful ingestion:

```
rows_loaded == rows_read
```

### rows_loaded

`rows_loaded` means the number of rows successfully committed to the corresponding raw table.

If the raw database transaction fails, the expected value is:

```
rows_loaded = 0
```

because the raw loader rolls back the entire load transaction.

For read/schema-validation failures:

```
rows_loaded = 0
```

## Failure Contract

Every expected ingestion failure must result in a failed source and failed run whenever the metadata database remains available.

Expected failures include:

- unsupported source name
- missing source file
- source path is not a file
- CSV parsing failure
- source schema mismatch
- raw database loading failure
- metadata lifecycle failure

### File/read failure

If the source cannot be read:

```
source_status = FAILED
run status = FAILED
rows_read = 0
rows_loaded = 0
```

The error message must identify the source and preserve the underlying cause where applicable.

### Schema-validation failure

If the file is readable but the source schema is invalid:

```
source_status = FAILED
run status = FAILED
rows_read = parsed row count
rows_loaded = 0
```

No raw rows may be loaded.

### Raw-load failure

If reading and schema validation succeed but the raw load fails:

```
source_status = FAILED
run status = FAILED
rows_read = parsed row count
rows_loaded = 0
```

The raw loader's transaction rollback guarantees that partially loaded batches are not counted as committed rows.

### Metadata failure

If the metadata database operation itself fails, the orchestration must not claim successful ingestion.

The underlying database exception must be preserved as the exception cause.

If metadata cannot be updated after the raw load has completed, the implementation must surface that failure rather than silently returning success. Such a case may leave metadata in a non-terminal state and must remain observable for later operational handling.

## Lifecycle Contract

### Run lifecycle

```
RUNNING ──► SUCCESS
    │
    └──────► FAILED
```

No terminal run may transition to another state.

### Source lifecycle

```
PENDING ──► SUCCESS
    │
    └──────► FAILED
```

No terminal source may transition to another state.

The existing lifecycle functions are the enforcement boundary:

- `complete_ingestion_run()`
- `fail_ingestion_run()`
- `complete_ingestion_source()`
- `fail_ingestion_source()`

The orchestration layer must not bypass these lifecycle functions with direct status updates.

## Single-Source Consistency Contract

3H.5.6 initially handles exactly one source file per ingestion run.

Therefore, on a successful operation:

```
run.status == SUCCESS
source.source_status == SUCCESS
run.rows_read == source.rows_read
run.rows_loaded == source.rows_loaded
```

On a failed operation:

```
run.status == FAILED
source.source_status == FAILED
run.rows_read == source.rows_read
run.rows_loaded == source.rows_loaded
```

The parent/child relationship must remain intact through:

```
ingestion_runs.ingestion_run_id
        │
        ▼
ingestion_sources.ingestion_run_id
```

## Result Contract

The orchestration operation should return a structured result rather than requiring callers to query PostgreSQL to determine whether the operation succeeded.

The logical result must expose at least:

| Field | Meaning |
|---|---|
| `ingestion_run_id` | Parent ingestion run identifier |
| `ingestion_source_id` | Source metadata identifier |
| `source_name` | DataPulse source name |
| `source_file_path` | Processed file |
| `status` | Final source/run outcome |
| `rows_read` | Parsed source row count |
| `rows_loaded` | Committed raw row count |
| `error_message` | Failure reason, otherwise NULL |

The exact Python representation will be defined during implementation.

## Atomicity Boundary

The orchestration consists of multiple database transactions:

1. metadata run creation
2. metadata source creation
3. raw data loading
4. metadata status update

The raw data load remains atomic within its own database transaction.

The entire orchestration is **not** treated as one PostgreSQL transaction because metadata creation, raw loading, and lifecycle updates have different responsibilities and the current loader contract explicitly owns the raw-load transaction.

The implementation must therefore prioritize **truthful operational state** over pretending the entire workflow is globally atomic.

## Contract Invariants

The implementation must preserve these invariants:

1. A source cannot become `SUCCESS` without a successful raw load.
2. A source cannot become `SUCCESS` if schema validation failed.
3. A failed raw transaction produces `rows_loaded = 0`.
4. Negative row counts are never written.
5. Terminal source states cannot transition again.
6. Terminal run states cannot transition again.
7. Every source belongs to exactly one ingestion run.
8. A successful single-source run has matching run/source row counts.
9. Errors retain their underlying exception as `__cause__` where database exceptions are wrapped.
10. The orchestration must never silently report success after an expected failure.
11. Source metadata exists even when the source file cannot be read.
12. Raw source data remains source-faithful; orchestration does not perform business transformations.

## Testing Requirements

3H.5.6 implementation tests must eventually cover:

### Success

- run created as `RUNNING`
- source created as `PENDING`
- CSV read
- schema validation
- raw load
- source becomes `SUCCESS`
- run becomes `SUCCESS`
- row counts match
- raw rows exist

### Failure

- missing file
- invalid source schema
- CSV parsing failure
- raw database failure
- terminal-state transition protection
- metadata database failure

### Consistency

- parent/child metadata relationship
- correct `rows_read`
- correct `rows_loaded`
- zero committed rows after raw-load rollback
- useful error messages
- preserved exception causes

### Integration

At least one successful and one failed orchestration path must be validated against the real Docker PostgreSQL instance.

## Implementation Boundary

This contract intentionally does not prescribe the final class/function names.

Implementation begins in:

- **3H.5.6.2 — Add ingestion source creation**
- **3H.5.6.3 — Build single-source ingestion workflow**
- **3H.5.6.4 — Integrate failure handling**

The contract should be treated as the acceptance criteria for those implementation steps.
