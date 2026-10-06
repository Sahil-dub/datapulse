CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.customers (
    raw_record_id BIGINT,
    customer_id TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    country TEXT,
    signup_date DATE,
    signup_date_parse_valid BOOLEAN,
    customer_status TEXT,
    acquisition_channel TEXT,

    CONSTRAINT pk_staging_customers PRIMARY KEY (raw_record_id)
);