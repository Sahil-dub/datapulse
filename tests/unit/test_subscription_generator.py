import pandas as pd

from datapulse.data_generation.config import DataGenerationConfig
from datapulse.data_generation.sources.customers import generate_customers
from datapulse.data_generation.sources.subscriptions import (
    expected_subscription_columns,
    generate_subscriptions,
)


def make_config(seed: int = 42) -> DataGenerationConfig:
    return DataGenerationConfig(
        subscriptions_count=500,
        customers_count=100,
        products_count=20,
        orders_count=100,
        payments_count=100,
        support_tickets_count=100,
        web_events_count=100,
        seed=seed,
    )


def make_customers(config: DataGenerationConfig) -> pd.DataFrame:
    return generate_customers(config)


def test_expected_subscription_columns() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert list(subscriptions.columns) == expected_subscription_columns()


def test_subscription_volume() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert len(subscriptions) == config.subscriptions_count


def test_subscription_ids_contain_duplicates() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert subscriptions["subscription_id"].duplicated().sum() > 0


def test_missing_customer_references_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert subscriptions["customer_id"].isna().sum() > 0


def test_invalid_customer_references_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert (subscriptions["customer_id"] == "UNKNOWN_CUSTOMER").sum() > 0


def test_invalid_plans_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert (subscriptions["plan_type"] == "UNKNOWN_PLAN").sum() > 0


def test_invalid_statuses_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert (subscriptions["subscription_status"] == "UNKNOWN_STATUS").sum() > 0


def test_invalid_billing_frequencies_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert (subscriptions["billing_frequency"] == "UNKNOWN_FREQUENCY").sum() > 0


def test_invalid_monthly_fees_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    assert (subscriptions["monthly_fee"] < 0).sum() > 0


def test_invalid_date_relationships_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    invalid_dates = subscriptions["end_date"].notna() & (
        subscriptions["end_date"] < subscriptions["start_date"]
    )

    assert invalid_dates.any()


def test_delayed_source_updates_exist() -> None:
    config = make_config()
    customers = make_customers(config)

    subscriptions = generate_subscriptions(config, customers)

    latency = subscriptions["source_updated_at"] - subscriptions["start_date"]

    assert (latency >= pd.Timedelta(3, unit="D")).any()


def test_generation_is_reproducible() -> None:
    config = make_config(seed=42)
    customers = make_customers(config)

    first = generate_subscriptions(config, customers)
    second = generate_subscriptions(config, customers)

    pd.testing.assert_frame_equal(first, second)


def test_different_seeds_produce_different_data() -> None:
    config_one = make_config(seed=42)
    config_two = make_config(seed=99)

    customers_one = make_customers(config_one)
    customers_two = make_customers(config_two)

    first = generate_subscriptions(config_one, customers_one)
    second = generate_subscriptions(config_two, customers_two)

    assert not first.equals(second)
