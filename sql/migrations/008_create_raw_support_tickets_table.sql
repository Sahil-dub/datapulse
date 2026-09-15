CREATE TABLE IF NOT EXISTS raw.support_tickets (
    raw_record_id BIGINT GENERATED ALWAYS AS IDENTITY,
    ticket_id TEXT,
    customer_id TEXT,
    ticket_created_at TEXT,
    ticket_updated_at TEXT,
    ticket_category TEXT,
    priority TEXT,
    ticket_status TEXT,
    resolution_channel TEXT,
    assigned_team TEXT,
    resolution_time_hours TEXT,
    customer_satisfaction_score TEXT,
    CONSTRAINT pk_support_tickets PRIMARY KEY (raw_record_id)
);