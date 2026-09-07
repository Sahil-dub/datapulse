CREATE TABLE IF NOT EXISTS raw.products (
    raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    product_id TEXT,
    product_name TEXT,
    category TEXT,
    unit_price TEXT,
    product_status TEXT,
    created_date TEXT,
    CONSTRAINT pk_products PRIMARY KEY (raw_record_id)
);