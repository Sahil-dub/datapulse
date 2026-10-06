from datetime import date
from pathlib import Path

from sqlalchemy import text

from datapulse.database import create_database_engine
from datapulse.settings import Settings
from datapulse.staging.customers import stage_customer

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "sql" / "migrations"


def _apply_migrations(engine) -> None:
    for migration_name in (
        "001_create_raw_schema.sql",
        "003_create_raw_customers_table.sql",
        "013_create_staging_customers_table.sql",
    ):
        migration_sql = (MIGRATIONS_DIR / migration_name).read_text(encoding="utf-8")
        with engine.begin() as connection:
            connection.execute(text(migration_sql))


def _cleanup(engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM staging.customers "
                "WHERE raw_record_id IN ("
                "SELECT raw_record_id FROM raw.customers "
                "WHERE customer_id LIKE 'STG-CUST-%'"
                ")"
            )
        )
        connection.execute(
            text("DELETE FROM raw.customers WHERE customer_id LIKE 'STG-CUST-%'")
        )


def test_stage_customer_preserves_traceability_and_types() -> None:
    engine = create_database_engine(Settings())
    _apply_migrations(engine)

    try:
        with engine.begin() as connection:
            raw_record_id = connection.execute(
                text(
                    """
                    INSERT INTO raw.customers (
                        customer_id, first_name, last_name, email, country,
                        signup_date, customer_status, acquisition_channel
                    ) VALUES (
                        'STG-CUST-001', ' Test ', ' User ', 'test@example.com', 'DE',
                        '2025-04-01', 'active', 'organic'
                    )
                    RETURNING raw_record_id
                    """
                )
            ).scalar_one()

        stage_customer(engine, raw_record_id)

        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT raw_record_id, customer_id, first_name, signup_date,
                           signup_date_parse_valid
                    FROM staging.customers
                    WHERE raw_record_id = :raw_record_id
                    """
                ),
                {"raw_record_id": raw_record_id},
            ).one()

        assert tuple(row) == (
            raw_record_id,
            "STG-CUST-001",
            "Test",
            date(2025, 4, 1),
            True,
        )
    finally:
        _cleanup(engine)
        engine.dispose()


def test_stage_customer_exposes_invalid_and_missing_signup_dates() -> None:
    engine = create_database_engine(Settings())
    _apply_migrations(engine)

    try:
        with engine.begin() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                        INSERT INTO raw.customers (customer_id, signup_date)
                        VALUES ('STG-CUST-INVALID', '2025-02-30'),
                               ('STG-CUST-MISSING', NULL)
                        RETURNING raw_record_id
                        """
                    )
                )
                .scalars()
                .all()
            )

        for raw_record_id in rows:
            stage_customer(engine, raw_record_id)

        with engine.connect() as connection:
            staged = connection.execute(
                text(
                    """
                    SELECT customer_id, signup_date, signup_date_parse_valid
                    FROM staging.customers
                    WHERE raw_record_id IN (:first_id, :second_id)
                    ORDER BY customer_id
                    """
                ),
                {"first_id": rows[0], "second_id": rows[1]},
            ).all()

        assert [tuple(row) for row in staged] == [
            ("STG-CUST-INVALID", None, False),
            ("STG-CUST-MISSING", None, None),
        ]
    finally:
        _cleanup(engine)
        engine.dispose()


def test_stage_customer_preserves_duplicate_business_ids() -> None:
    engine = create_database_engine(Settings())
    _apply_migrations(engine)

    try:
        with engine.begin() as connection:
            rows = (
                connection.execute(
                    text(
                        """
                        INSERT INTO raw.customers (customer_id, signup_date)
                        VALUES ('STG-CUST-DUP', '2025-01-01'),
                               ('STG-CUST-DUP', '2025-01-02')
                        RETURNING raw_record_id
                        """
                    )
                )
                .scalars()
                .all()
            )

        for raw_record_id in rows:
            stage_customer(engine, raw_record_id)

        with engine.connect() as connection:
            result = connection.execute(
                text(
                    """
                    SELECT raw_record_id, customer_id
                    FROM staging.customers
                    WHERE customer_id = 'STG-CUST-DUP'
                    ORDER BY raw_record_id
                    """
                )
            ).all()

        assert [tuple(row) for row in result] == [
            (rows[0], "STG-CUST-DUP"),
            (rows[1], "STG-CUST-DUP"),
        ]
    finally:
        _cleanup(engine)
        engine.dispose()
