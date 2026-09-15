CREATE TABLE IF NOT EXISTS metadata.ingestion_runs (
    ingestion_run_id BIGINT GENERATED ALWAYS AS IDENTITY,
    source_name TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    rows_read BIGINT NOT NULL DEFAULT 0,
    rows_loaded BIGINT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_ingestion_runs PRIMARY KEY (ingestion_run_id),
    CONSTRAINT ck_ingestion_runs_status
        CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    CONSTRAINT ck_ingestion_runs_rows_read
        CHECK (rows_read >= 0),
    CONSTRAINT ck_ingestion_runs_rows_loaded
        CHECK (rows_loaded >= 0),
    CONSTRAINT ck_ingestion_runs_finished_at
        CHECK (finished_at IS NULL OR finished_at >= started_at)
);