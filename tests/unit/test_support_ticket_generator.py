import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.support_tickets import (
    expected_support_ticket_columns,
    generate_support_tickets,
)


def make_config(seed: int = 42) -> DataGenerationConfig:
    return DataGenerationConfig(
        subscriptions_count=100,
        customers_count=100,
        products_count=20,
        orders_count=100,
        payments_count=100,
        support_tickets_count=500,
        web_events_count=100,
        seed=seed,
    )


def test_expected_support_ticket_columns() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert list(tickets.columns) == expected_support_ticket_columns()


def test_support_ticket_volume() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert len(tickets) == config.support_tickets_count


def test_duplicate_ticket_ids_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert tickets["ticket_id"].duplicated().sum() > 0


def test_missing_customer_references_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert tickets["customer_id"].isna().sum() > 0


def test_invalid_customer_references_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["customer_id"] == "UNKNOWN_CUSTOMER").sum() > 0


def test_invalid_categories_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["ticket_category"] == "UNKNOWN_CATEGORY").sum() > 0


def test_invalid_priorities_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["priority"] == "UNKNOWN_PRIORITY").sum() > 0


def test_invalid_statuses_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["ticket_status"] == "UNKNOWN_STATUS").sum() > 0


def test_invalid_resolution_channels_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["resolution_channel"] == "UNKNOWN_CHANNEL").sum() > 0


def test_invalid_assigned_teams_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["assigned_team"] == "UNKNOWN_TEAM").sum() > 0


def test_invalid_resolution_times_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["resolution_time_hours"] < 0).sum() > 0
    assert (tickets["resolution_time_hours"] > 1000).sum() > 0


def test_timestamp_inconsistencies_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    invalid_timestamps = tickets["ticket_updated_at"] < tickets["ticket_created_at"]

    assert invalid_timestamps.any()


def test_invalid_satisfaction_scores_exist() -> None:
    config = make_config()
    customers = generate_customers(config)

    tickets = generate_support_tickets(config, customers)

    assert (tickets["customer_satisfaction_score"] == 0).sum() > 0


def test_generation_is_reproducible() -> None:
    config = make_config(seed=42)
    customers = generate_customers(config)

    first = generate_support_tickets(config, customers)
    second = generate_support_tickets(config, customers)

    pd.testing.assert_frame_equal(first, second)


def test_different_seeds_produce_different_data() -> None:
    config_one = make_config(seed=42)
    config_two = make_config(seed=99)

    customers_one = generate_customers(config_one)
    customers_two = generate_customers(config_two)

    first = generate_support_tickets(config_one, customers_one)
    second = generate_support_tickets(config_two, customers_two)

    assert not first.equals(second)
