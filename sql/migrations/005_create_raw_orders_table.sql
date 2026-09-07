CREATE TABLE IF NOT EXISTS raw.orders (
    raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    order_id TEXT,
    customer_id TEXT,
    product_id TEXT,
    order_date TEXT,
    quantity TEXT,
    unit_price TEXT,
    discount_amount TEXT,
    shipping_amount TEXT,
    order_total TEXT,
    order_status TEXT,
    sales_channel TEXT,
    CONSTRAINT pk_orders PRIMARY KEY (raw_record_id)
);