from pathlib import Path

import pandas as pd
from sqlalchemy import text

from datapulse.database import create_database_engine
from datapulse.ingestion_contract import IngestionOutcome, IngestionRequest
from datapulse.ingestion_orchestrator import ingest_source
from datapulse.settings import Settings


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "customers_integration.csv"
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


def _cleanup_success_data(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM raw.customers "
                "WHERE customer_id LIKE 'INT-CUST-%'"
            )
        )
        connection.execute(
            text(
                "DELETE FROM metadata.ingestion_sources "
                "WHERE source_file_path = :source_file_path"
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


def _cleanup_failure_data(engine, source_file_path: Path) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM metadata.ingestion_sources "
                "WHERE source_file_path = :source_file_path"
            ),
            {"source_file_path": str(source_file_path)},
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


def test_ingest_source_completes_real_postgres_successfully() -> None:
    engine = _create_integration_engine()
    _apply_integration_migrations(engine)

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

        assert result.outcome is IngestionOutcome.SUCCESS
        assert result.rows_read == expected_rows
        assert result.rows_loaded == expected_rows
        assert result.error_message is None

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
                text(
                    "SELECT COUNT(*) "
                    "FROM raw.customers "
                    "WHERE customer_id LIKE 'INT-CUST-%'"
                )
            ).scalar_one()

        assert tuple(run_row) == ("SUCCESS", expected_rows, expected_rows, None)
        assert tuple(source_row) == ("SUCCESS", expected_rows, expected_rows, None)
        assert raw_count == expected_rows
    finally:
        _cleanup_success_data(engine)
        engine.dispose()


def test_ingest_source_records_real_postgres_schema_failure() -> None:
    engine = _create_integration_engine()
    _apply_integration_migrations(engine)

    invalid_path = FIXTURE_PATH.parent / "customers_integration_invalid.csv"
    invalid_path.write_text(
        "customer_id,first_name,last_name,email,country,signup_date,customer_status\n"
        "INT-CUST-FAIL,Test,User,test.integration@example.com,DE,2025-04-01,active\n",
        encoding="utf-8",
    )

    try:
        result = ingest_source(
            engine,
            IngestionRequest(
                source_name="customers",
                source_file_path=invalid_path,
            ),
        )

        assert result.outcome is IngestionOutcome.FAILED
        assert result.rows_read == 1
        assert result.rows_loaded == 0
        assert result.error_message is not None

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
                text(
                    "SELECT COUNT(*) "
                    "FROM raw.customers "
                    "WHERE customer_id = 'INT-CUST-FAIL'"
                )
            ).scalar_one()

        assert run_row[0] == "FAILED"
        assert run_row[1:3] == (1, 0)
        assert run_row[3] == result.error_message
        assert source_row[0] == "FAILED"
        assert source_row[1:3] == (1, 0)
        assert source_row[3] == result.error_message
        assert raw_count == 0
    finally:
        invalid_path.unlink(missing_ok=True)
        _cleanup_failure_data(engine, invalid_path)
        engine.dispose()
