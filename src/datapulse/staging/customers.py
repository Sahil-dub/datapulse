from sqlalchemy import Engine, text

CUSTOMER_STAGING_SQL = text("SELECT 1")

def stage_customer(engine: Engine, raw_record_id: int) -> None:
    """Transform one raw customer record into its staging representation."""
    with engine.begin() as connection:
        connection.execute(CUSTOMER_STAGING_SQL)
