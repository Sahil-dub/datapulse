from sqlalchemy import Engine, text

CUSTOMER_STAGING_SQL = text(
    """
    INSERT INTO staging.customers (
        raw_record_id, customer_id, first_name, last_name, email, country,
        signup_date, signup_date_parse_valid, customer_status, acquisition_channel
    )
    SELECT
        raw_record_id,
        NULLIF(BTRIM(customer_id), ''),
        NULLIF(BTRIM(first_name), ''),
        NULLIF(BTRIM(last_name), ''),
        NULLIF(BTRIM(email), ''),
        NULLIF(BTRIM(country), ''),
        CASE
            WHEN signup_date IS NULL OR BTRIM(signup_date) = '' THEN NULL
            WHEN BTRIM(signup_date) ~ '^\\d{4}-\\d{2}-\\d{2}$'
                AND split_part(BTRIM(signup_date), '-', 2)::INTEGER BETWEEN 1 AND 12
                AND split_part(BTRIM(signup_date), '-', 3)::INTEGER >= 1
                AND split_part(BTRIM(signup_date), '-', 3)::INTEGER <=
                    CASE split_part(BTRIM(signup_date), '-', 2)::INTEGER
                        WHEN 2 THEN
                            28 + CASE
                                WHEN split_part(BTRIM(signup_date), '-', 1)::INTEGER % 400 = 0
                                    OR (
                                        split_part(BTRIM(signup_date), '-', 1)::INTEGER % 4 = 0
                                        AND split_part(BTRIM(signup_date), '-', 1)::INTEGER % 100 <> 0
                                    )
                                THEN 1 ELSE 0
                            END
                        WHEN 4, 6, 9, 11 THEN 30
                        ELSE 31
                    END
            THEN TO_DATE(BTRIM(signup_date), 'YYYY-MM-DD')
            ELSE NULL
        END,
        CASE
            WHEN signup_date IS NULL OR BTRIM(signup_date) = '' THEN NULL
            WHEN BTRIM(signup_date) ~ '^\\d{4}-\\d{2}-\\d{2}$'
                AND split_part(BTRIM(signup_date), '-', 2)::INTEGER BETWEEN 1 AND 12
                AND split_part(BTRIM(signup_date), '-', 3)::INTEGER >= 1
                AND split_part(BTRIM(signup_date), '-', 3)::INTEGER <=
                    CASE split_part(BTRIM(signup_date), '-', 2)::INTEGER
                        WHEN 2 THEN
                            28 + CASE
                                WHEN split_part(BTRIM(signup_date), '-', 1)::INTEGER % 400 = 0
                                    OR (
                                        split_part(BTRIM(signup_date), '-', 1)::INTEGER % 4 = 0
                                        AND split_part(BTRIM(signup_date), '-', 1)::INTEGER % 100 <> 0
                                    )
                                THEN 1 ELSE 0
                            END
                        WHEN 4, 6, 9, 11 THEN 30
                        ELSE 31
                    END
            THEN TRUE
            ELSE FALSE
        END,
        NULLIF(BTRIM(customer_status), ''),
        NULLIF(BTRIM(acquisition_channel), '')
    FROM raw.customers
    WHERE raw_record_id = :raw_record_id
    """
)


def stage_customer(engine: Engine, raw_record_id: int) -> None:
    """Transform one raw customer record into its staging representation."""
    with engine.begin() as connection:
        connection.execute(CUSTOMER_STAGING_SQL, {"raw_record_id": raw_record_id})
