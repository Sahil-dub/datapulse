ALTER TABLE metadata.ingestion_sources
    ADD COLUMN IF NOT EXISTS rows_read BIGINT NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS rows_loaded BIGINT NOT NULL DEFAULT 0;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_ingestion_sources_rows_read'
          AND conrelid = 'metadata.ingestion_sources'::regclass
    ) THEN
        ALTER TABLE metadata.ingestion_sources
            ADD CONSTRAINT ck_ingestion_sources_rows_read
            CHECK (rows_read >= 0);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_ingestion_sources_rows_loaded'
          AND conrelid = 'metadata.ingestion_sources'::regclass
    ) THEN
        ALTER TABLE metadata.ingestion_sources
            ADD CONSTRAINT ck_ingestion_sources_rows_loaded
            CHECK (rows_loaded >= 0);
    END IF;
END
$$;