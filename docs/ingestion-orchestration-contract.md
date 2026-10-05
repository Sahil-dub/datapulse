# Ingestion Orchestration Contract

## Scope

3H.5.6.1 defines the contract for a single-source ingestion workflow.

This milestone does not implement orchestration, file I/O, database writes, or metadata state transitions.

## Request

The workflow accepts an immutable `IngestionRequest`:

- `source_name`: logical DataPulse source name, such as `customers`
- `source_file_path`: path to the source CSV file

The request identifies one source file for one ingestion operation.

## Result

A completed workflow returns an immutable `IngestionResult`:

- `ingestion_run_id`: parent ingestion run identifier
- `ingestion_source_id`: source-level metadata identifier
- `source_name`: logical source name
- `source_file_path`: ingested source file path
- `outcome`: `SUCCESS` or `FAILED`
- `rows_read`: number of rows read from the source file
- `rows_loaded`: number of rows successfully loaded into the raw table
- `error_message`: `NULL`/Python `None` for success; useful failure description for failure

## Outcome Semantics

### SUCCESS

A successful result means:

1. the source file was readable;
2. source schema validation passed;
3. raw loading completed successfully;
4. the raw database transaction committed;
5. source metadata was recorded as `SUCCESS`;
6. run metadata was recorded as `SUCCESS`.

### FAILED

A failed result means the workflow could not complete successfully.

The result must preserve the work actually performed:

- `rows_read` reflects rows read before the failure;
- `rows_loaded` reflects rows committed to the raw table;
- `error_message` explains the failure.

A raw database transaction failure must not report rows as loaded when that transaction was rolled back.

## Ownership

The future orchestrator coordinates existing components:

`IngestionRequest` → file reader → CSV validation → metadata registration → raw loader → metadata completion → `IngestionResult`

Component responsibilities remain separate:

- file reader: read source data;
- CSV validator: validate source structure;
- raw loader: load data transactionally;
- ingestion metadata: persist lifecycle state;
- orchestrator: coordinate the workflow and translate component outcomes into the contract.

## Explicit Non-Goals

3H.5.6.1 does not introduce:

- multi-source orchestration;
- retries;
- scheduling;
- asynchronous execution;
- external job queues;
- new database tables;
- changes to raw-table contracts;
- automatic data-quality remediation.
