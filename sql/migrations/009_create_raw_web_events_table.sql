CREATE TABLE IF NOT EXISTS raw.web_events (
    raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    event_id TEXT,
    event_timestamp TEXT,
    source_received_at TEXT,
    session_id TEXT,
    customer_id TEXT,
    event_type TEXT,
    page_type TEXT,
    device_type TEXT,
    traffic_source TEXT,
    product_id TEXT,
    order_id TEXT,
    revenue_amount TEXT,
    CONSTRAINT pk_web_events PRIMARY KEY (raw_record_id)
);