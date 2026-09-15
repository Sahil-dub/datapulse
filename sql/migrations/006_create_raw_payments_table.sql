CREATE TABLE IF NOT EXISTS raw.payments (
    raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    payment_id TEXT,
    order_id TEXT,
    payment_date TEXT,
    payment_method TEXT,
    payment_amount TEXT,
    payment_status TEXT,
    transaction_reference TEXT,
    currency TEXT,
    source_updated_at TEXT,
    CONSTRAINT pk_payments PRIMARY KEY (raw_record_id)
);