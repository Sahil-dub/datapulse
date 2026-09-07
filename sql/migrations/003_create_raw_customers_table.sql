CREATE TABLE IF NOT EXISTS raw.customers (
    raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    customer_id TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    country TEXT,
    signup_date TEXT,
    customer_status TEXT,
    acquisition_channel TEXT,
    CONSTRAINT pk_customers PRIMARY KEY (raw_record_id)
);