CREATE TABLE IF NOT EXISTS metadata.ingestion_sources (
    ingestion_source_id BIGINT GENERATED ALWAYS AS IDENTITY,
    ingestion_run_id BIGINT NOT NULL,
    source_name TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    source_file_path TEXT NOT NULL,
    source_status TEXT NOT NULL DEFAULT 'PENDING',
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    error_message TEXT,

    CONSTRAINT pk_ingestion_sources
        PRIMARY KEY (ingestion_source_id),

    CONSTRAINT fk_ingestion_sources_ingestion_runs
        FOREIGN KEY (ingestion_run_id)
        REFERENCES metadata.ingestion_runs (ingestion_run_id),

    CONSTRAINT uq_ingestion_sources_run_file
        UNIQUE (ingestion_run_id, source_file_path),

    CONSTRAINT ck_ingestion_sources_status
        CHECK (source_status IN ('PENDING', 'SUCCESS', 'FAILED')),

    CONSTRAINT ck_ingestion_sources_finished_at
        CHECK (finished_at IS NULL OR finished_at >= started_at)
);