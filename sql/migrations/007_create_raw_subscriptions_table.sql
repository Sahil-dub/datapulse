CREATE TABLE IF NOT EXISTS raw.subscriptions (
    raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    subscription_id TEXT,
    customer_id TEXT,
    plan_type TEXT,
    subscription_status TEXT,
    billing_frequency TEXT,
    start_date TEXT,
    end_date TEXT,
    monthly_fee TEXT,
    auto_renew TEXT,
    source_updated_at TEXT,
    CONSTRAINT pk_subscriptions PRIMARY KEY (raw_record_id)
);