# DataPulse Ingestion Orchestration Contract

## Status

**Implemented and validated — Phase 3**

The ingestion orchestration contract was originally defined in 3H.5.6.1 and was subsequently implemented and validated through the remaining 3H.5.6 milestones.

The current implementation provides a single-source ingestion workflow backed by PostgreSQL.

---

## Purpose

The ingestion orchestration layer coordinates one source-file ingestion operation and ensures that operational metadata accurately describes what happened.

The orchestration connects:

```text
source file
    ↓
ingestion run
    ↓
ingestion source
    ↓
CSV reader
    ↓
CSV schema validation
    ↓
raw database loader
    ↓
metadata completion
```

Failure paths are represented explicitly:

```text
failure
   ↓
source FAILED
   ↓
run FAILED
```

The orchestration layer does not perform business transformations.

---

## Scope

### In scope

- one source file per ingestion operation
- ingestion run creation
- ingestion source creation
- CSV file reading
- source schema validation
- raw-table loading
- row-count tracking
- source lifecycle updates
- run lifecycle updates
- failure capture
- deterministic ingestion result
- PostgreSQL transaction handling through the raw loader

### Out of scope

- staging transformations
- business transformations
- business analytics
- anomaly detection
- root-cause analysis
- retries
- scheduling
- parallel ingestion
- external orchestration platforms
- API exposure
- automatic data-quality remediation

These belong to later phases.

---

## Supported Sources

| Source | Raw table |
|---|---|
| `customers` | `raw.customers` |
| `products` | `raw.products` |
| `orders` | `raw.orders` |
| `payments` | `raw.payments` |
| `subscriptions` | `raw.subscriptions` |
| `support_tickets` | `raw.support_tickets` |
| `web_events` | `raw.web_events` |

The source-to-table mapping is controlled by the application rather than dynamically constructing table names from untrusted input.

---

## Request Contract

A single-source ingestion request contains:

```text
source_name
source_file_path
```

The Python contract is represented by:

```python
@dataclass(frozen=True)
class IngestionRequest:
    source_name: str
    source_file_path: Path
```

The request identifies exactly one source file for one ingestion operation.

---

## Result Contract

A completed workflow returns a structured result containing:

```python
@dataclass(frozen=True)
class IngestionResult:
    ingestion_run_id: int
    ingestion_source_id: int
    source_name: str
    source_file_path: Path
    outcome: IngestionOutcome
    rows_read: int
    rows_loaded: int
    error_message: str | None = None
```

Possible outcomes are:

```text
SUCCESS
FAILED
```

---

## Processing Workflow

### 1. Create ingestion run

A record is created in:

```text
metadata.ingestion_runs
```

with:

```text
status = RUNNING
```

Initial row counts are zero.

### 2. Create ingestion source

A child record is created in:

```text
metadata.ingestion_sources
```

with:

```text
source_status = PENDING
```

The source belongs to the parent ingestion run through `ingestion_run_id`.

### 3. Read source CSV

The existing CSV reader reads the source file.

Source values are preserved as strings so invalid source values remain observable for downstream validation.

### 4. Validate CSV schema

The source is validated against the expected source schema.

Validation covers:

- required columns
- unexpected columns
- duplicate headers
- column ordering

If validation fails, the raw table is not modified.

### 5. Load raw data

The validated DataFrame is passed to the raw database loader.

The raw loader supports batched loading.

All batches belonging to one raw load operation execute inside one database transaction.

### 6. Record success

After the raw transaction commits:

- source becomes `SUCCESS`
- run becomes `SUCCESS`
- completion timestamps are recorded
- row counts are recorded
- error information remains empty

---

## Row Counts

### rows_read

`rows_read` is the number of data rows successfully parsed from the CSV.

The header row is not counted.

### rows_loaded

`rows_loaded` is the number of rows successfully committed to the raw table.

For successful ingestion:

```text
rows_loaded == rows_read
```

For a raw database transaction failure:

```text
rows_loaded == 0
```

because the complete raw-load transaction is rolled back.

For read or schema-validation failures:

```text
rows_loaded == 0
```

---

## Failure Handling

Expected ingestion failures are represented as failed ingestion operations.

Examples include:

- missing source file
- invalid source path
- CSV parsing failure
- schema mismatch
- raw database failure

For a file or parsing failure:

```text
source_status = FAILED
run status = FAILED
rows_loaded = 0
```

For a schema validation failure:

```text
source_status = FAILED
run status = FAILED
rows_read = parsed row count
rows_loaded = 0
```

For a raw database failure:

```text
source_status = FAILED
run status = FAILED
rows_read = parsed row count
rows_loaded = 0
```

The underlying database error is preserved in the resulting error information and exception chain.

---

## Transaction Boundary

The ingestion workflow contains multiple database operations.

The raw data load itself is atomic.

For example:

```text
batch 1
   ↓
batch 2
   ↓
batch 3
   ↓
commit
```

If batch 3 fails:

```text
batch 1
   ↓
batch 2
   ↓
batch 3 FAILED
   ↓
ROLLBACK
```

Previously inserted batches from the same raw-load operation are not left partially committed.

The entire orchestration is not treated as one global PostgreSQL transaction because metadata lifecycle operations and raw loading have separate responsibilities.

---

## Lifecycle

### Ingestion run

```text
RUNNING
   ├──→ SUCCESS
   └──→ FAILED
```

### Ingestion source

```text
PENDING
   ├──→ SUCCESS
   └──→ FAILED
```

Terminal states cannot be transitioned again.

Lifecycle updates are performed through the ingestion metadata functions rather than direct status manipulation inside the orchestrator.

---

## Consistency Rules

For successful ingestion:

```text
run.status == SUCCESS
source.source_status == SUCCESS
run.rows_read == source.rows_read
run.rows_loaded == source.rows_loaded
```

For failed ingestion:

```text
run.status == FAILED
source.source_status == FAILED
run.rows_read == source.rows_read
run.rows_loaded == source.rows_loaded
```

The parent-child metadata relationship must remain intact.

---

## Invariants

The implementation must preserve:

1. A source cannot become `SUCCESS` without a successful raw load.
2. Schema validation must succeed before raw loading begins.
3. A failed raw transaction results in zero committed rows.
4. Negative row counts are never written.
5. Terminal states cannot transition again.
6. Every ingestion source belongs to an ingestion run.
7. Successful run/source row counts remain consistent.
8. Database errors retain their underlying exception where applicable.
9. Expected ingestion failures must never be silently reported as successful.
10. Source metadata must exist even when the source file cannot be read.
11. Raw ingestion must remain source-faithful.
12. Business transformations do not belong in the raw ingestion layer.

---

## Validation

The orchestration implementation was validated with:

- unit tests
- integration tests
- real PostgreSQL execution
- successful ingestion
- schema validation failure
- database failure
- transaction rollback
- ingestion metadata validation
- row-count validation
- error-message validation

Final project regression validation:

```text
242 passed in 5.52s
```

Code quality validation:

```text
ruff format --check src tests
60 files already formatted

ruff check src tests
All checks passed!

git diff --check
```

---

## Implementation Components

The orchestration coordinates:

```text
file_reader.py
      ↓
csv_validation.py
      ↓
db_loader.py
      ↓
ingestion_metadata.py
      ↓
ingestion_orchestrator.py
```

The request/result contract is defined in:

```text
ingestion_contract.py
```

---

## Phase Boundary

The ingestion orchestration belongs to Phase 3.

Phase 3 is formally complete.

Future phases should consume the resulting raw data rather than expand the Phase 3 orchestration contract unless a genuine defect or production requirement is discovered.

The next major responsibility is warehouse data modelling.
