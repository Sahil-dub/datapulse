from pathlib import Path

import pandas as pd
from sqlalchemy import text

from datapulse.database import create_database_engine
from datapulse.ingestion_contract import IngestionOutcome, IngestionRequest
from datapulse.ingestion_orchestrator import ingest_source
from datapulse.settings import Settings

FIXTURE_PATH = (
    Path(__file__).resolve().parents[1] / "fixtures" / "customers_integration_db_failure.csv"
)
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


def _apply_integration_migrations(engine) -> None:
    migration_paths = (
        "001_create_raw_schema.sql",
        "002_create_metadata_schema.sql",
        "003_create_raw_customers_table.sql",
        "010_create_ingestion_runs_table.sql",
        "011_create_ingestion_sources_table.sql",
        "012_add_ingestion_source_row_counts.sql",
    )

    for migration_name in migration_paths:
        migration_sql = (MIGRATIONS_DIR / migration_name).read_text(encoding="utf-8")
        with engine.begin() as connection:
            connection.execute(text(migration_sql))


def _create_integration_engine():
    return create_database_engine(Settings())


def _install_failure_trigger(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE OR REPLACE FUNCTION datapulse_test_fail_customer_insert()
                RETURNS trigger
                LANGUAGE plpgsql
                AS $$
                BEGIN
                    IF NEW.customer_id = 'INT-CUST-DB-FAIL' THEN
                        RAISE EXCEPTION 'intentional PostgreSQL integration failure';
                    END IF;

                    RETURN NEW;
                END;
                $$;
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TRIGGER datapulse_test_fail_customer_insert_trigger
                BEFORE INSERT ON raw.customers
                FOR EACH ROW
                EXECUTE FUNCTION datapulse_test_fail_customer_insert();
                """
            )
        )


def _remove_failure_trigger(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                DROP TRIGGER IF EXISTS
                    datapulse_test_fail_customer_insert_trigger
                ON raw.customers;
                """
            )
        )
        connection.execute(text("DROP FUNCTION IF EXISTS datapulse_test_fail_customer_insert();"))


def _cleanup_data(engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM raw.customers WHERE customer_id LIKE 'INT-CUST-DB-%'"))
        connection.execute(
            text(
                "DELETE FROM metadata.ingestion_sources WHERE source_file_path = :source_file_path"
            ),
            {"source_file_path": str(FIXTURE_PATH)},
        )
        connection.execute(
            text(
                "DELETE FROM metadata.ingestion_runs "
                "WHERE source_name = 'customers' "
                "AND ingestion_run_id NOT IN ("
                "    SELECT DISTINCT ingestion_run_id "
                "    FROM metadata.ingestion_sources"
                ")"
            )
        )


def test_ingest_source_rolls_back_real_postgres_load_failure() -> None:
    engine = _create_integration_engine()
    _apply_integration_migrations(engine)
    _install_failure_trigger(engine)

    dataframe = pd.read_csv(FIXTURE_PATH, dtype="string")
    expected_rows = len(dataframe)

    try:
        result = ingest_source(
            engine,
            IngestionRequest(
                source_name="customers",
                source_file_path=FIXTURE_PATH,
            ),
            batch_size=2,
        )

        assert result.outcome is IngestionOutcome.FAILED
        assert result.rows_read == expected_rows
        assert result.rows_loaded == 0
        assert result.error_message is not None
        assert "batch 2" in result.error_message
        assert "intentional PostgreSQL integration failure" in result.error_message

        with engine.connect() as connection:
            run_row = connection.execute(
                text(
                    "SELECT status, rows_read, rows_loaded, error_message "
                    "FROM metadata.ingestion_runs "
                    "WHERE ingestion_run_id = :ingestion_run_id"
                ),
                {"ingestion_run_id": result.ingestion_run_id},
            ).one()

            source_row = connection.execute(
                text(
                    "SELECT source_status, rows_read, rows_loaded, error_message "
                    "FROM metadata.ingestion_sources "
                    "WHERE ingestion_source_id = :ingestion_source_id"
                ),
                {"ingestion_source_id": result.ingestion_source_id},
            ).one()

            raw_count = connection.execute(
                text("SELECT COUNT(*) FROM raw.customers WHERE customer_id LIKE 'INT-CUST-DB-%'")
            ).scalar_one()

        assert tuple(run_row) == (
            "FAILED",
            expected_rows,
            0,
            result.error_message,
        )
        assert tuple(source_row) == (
            "FAILED",
            expected_rows,
            0,
            result.error_message,
        )
        assert raw_count == 0
    finally:
        _remove_failure_trigger(engine)
        _cleanup_data(engine)
        engine.dispose()
